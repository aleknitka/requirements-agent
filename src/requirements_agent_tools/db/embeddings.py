"""Embedding generation, persistence, and vector search."""

from __future__ import annotations

import sqlite3

from loguru import logger

from .. import CONSTANTS as C
from ..models import RequirementRow
from . import _serialization as ser
from .requirements import get_requirement


def embed(text: str) -> list[float]:
    """Embed ``text`` with the configured OpenAI-compatible endpoint.

    Args:
        text: The text to embed.

    Returns:
        A list of floats of length :data:`CONSTANTS.EMBEDDING_DIM`.

    Raises:
        RuntimeError: If ``EMBEDDING_API_KEY`` is unset or the ``openai``
            package is not installed.
    """
    if not C.EMBEDDING_API_KEY:
        raise RuntimeError(
            "EMBEDDING_API_KEY is not set. "
            "Export OPENAI_API_KEY (or the relevant env var) before running."
        )
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "openai package not installed. Run: pip install openai"
        ) from e

    logger.debug("Embedding {} chars with model={}", len(text), C.EMBEDDING_MODEL)
    client = OpenAI(api_key=C.EMBEDDING_API_KEY, base_url=C.EMBEDDING_API_BASE)
    response = client.embeddings.create(model=C.EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def store_embedding(
    conn: sqlite3.Connection,
    req_id: str,
    title: str,
    description: str,
) -> None:
    """Generate and upsert an embedding for one requirement.

    Silently skips when no API key is configured. Embedding failures are
    logged as warnings but do not propagate — the row is already persisted.

    Args:
        conn: Open DB connection.
        req_id: Requirement identifier.
        title: Requirement title.
        description: Requirement description.
    """
    if not C.EMBEDDING_API_KEY:
        logger.debug("Skipping embedding for {} (no API key)", req_id)
        return
    try:
        vec = embed(f"{title}\n\n{description}".strip())
        blob = ser.vec_to_blob(vec)
        conn.execute(
            """
            INSERT INTO req_embeddings(requirement_id, embedding) VALUES (?, ?)
            ON CONFLICT(requirement_id) DO UPDATE SET embedding = excluded.embedding
            """,
            (req_id, blob),
        )
        # Also sync to virtual table if it exists
        has_vec = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='req_embeddings_vec'"
        ).fetchone()
        if has_vec:
            conn.execute(
                "INSERT OR REPLACE INTO req_embeddings_vec(requirement_id, embedding) VALUES (?, ?)",
                (req_id, blob),
            )

        logger.debug("Stored embedding for {}", req_id)
    except Exception as e:  # noqa: BLE001 — non-fatal
        logger.warning("Embedding generation failed for {}: {}", req_id, e)


def vector_search(
    conn: sqlite3.Connection,
    query_text: str,
    top_k: int = 10,
) -> list[tuple[RequirementRow, float]]:
    """Return the ``top_k`` requirements closest to ``query_text``.

    Args:
        conn: Open DB connection.
        query_text: Free-form query string; will be embedded with the
            configured model.
        top_k: Maximum number of hits to return.

    Returns:
        ``(RequirementRow, distance)`` tuples sorted by ascending distance.
    """
    has_vec = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='req_embeddings_vec'"
    ).fetchone()
    if not has_vec:
        logger.warning("Vector search requested but req_embeddings_vec table missing.")
        return []

    q_vec = embed(query_text)
    q_blob = ser.vec_to_blob(q_vec)

    vec_rows = conn.execute(
        """
        SELECT requirement_id, distance
        FROM req_embeddings_vec
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
        """,
        (q_blob, top_k),
    ).fetchall()

    results: list[tuple[RequirementRow, float]] = []
    for vec_row in vec_rows:
        req = get_requirement(conn, vec_row["requirement_id"])
        if req:
            results.append((req, vec_row["distance"]))
    logger.debug("vector_search returned {} hits", len(results))
    return results
