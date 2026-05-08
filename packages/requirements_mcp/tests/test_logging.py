"""Tests for ``requirements_mcp.logging.configure_logging``.

All file output is directed to ``tmp_path`` so no real log files are created
or left behind after the test session.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger

from requirements_mcp.logging import configure_logging


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _log_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.log"))


def test_creates_daily_file_in_log_dir(tmp_path: Path) -> None:
    configure_logging(name="t", log_dir=tmp_path, level="DEBUG")
    logger.info("hello daily")
    logger.complete()

    files = _log_files(tmp_path)
    assert len(files) == 1
    assert files[0].name == f"t-{_today()}.log"
    assert "hello daily" in files[0].read_text(encoding="utf-8")


def test_filename_uses_today_date(tmp_path: Path) -> None:
    configure_logging(name="dated", log_dir=tmp_path)
    logger.info("trigger file creation")
    logger.complete()

    files = _log_files(tmp_path)
    assert len(files) == 1
    stem = files[0].stem
    assert stem == f"dated-{_today()}"


def test_writes_to_stdout(tmp_path: Path, capsys) -> None:
    configure_logging(name="stdout_test", log_dir=tmp_path)
    logger.info("stdout message")
    logger.complete()

    captured = capsys.readouterr()
    assert "stdout message" in captured.out


def test_idempotent_no_duplicate_handlers(tmp_path: Path) -> None:
    configure_logging(name="idem", log_dir=tmp_path)
    configure_logging(name="idem", log_dir=tmp_path)
    logger.info("only-once")
    logger.complete()

    files = _log_files(tmp_path)
    assert len(files) == 1
    contents = files[0].read_text(encoding="utf-8")
    assert contents.count("only-once") == 1


def test_log_dir_created_if_missing(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "logs"
    assert not nested.exists()

    configure_logging(name="nested", log_dir=nested)
    logger.info("create me")
    logger.complete()

    assert nested.is_dir()
    files = _log_files(nested)
    assert len(files) == 1


def test_disable_file_sink(tmp_path: Path) -> None:
    configure_logging(name="no_file", log_dir=tmp_path, enable_file=False)
    logger.info("stdout only")
    logger.complete()

    assert _log_files(tmp_path) == []


def test_disable_stdout_sink(tmp_path: Path, capsys) -> None:
    configure_logging(name="no_stdout", log_dir=tmp_path, enable_stdout=False)
    logger.info("file only")
    logger.complete()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(_log_files(tmp_path)) == 1
