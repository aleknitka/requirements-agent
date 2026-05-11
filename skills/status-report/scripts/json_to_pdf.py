from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)


def json_to_pdf(data: dict[str, Any] | str, output_path: str | Path) -> Path:
    """
    Build a PDF from a JSON-like document structure.

    Supported JSON structure:

    {
        "title": "Report title",
        "metadata": {
            "Author": "Jane Doe",
            "Date": "2026-05-09"
        },
        "sections": [
            {
                "heading": "Introduction",
                "content": [
                    {"type": "paragraph", "text": "Some text here."},
                    {"type": "bullets", "items": ["Point one", "Point two"]},
                    {
                        "type": "table",
                        "headers": ["Name", "Value"],
                        "rows": [
                            ["A", 10],
                            ["B", 20]
                        ]
                    }
                ]
            }
        ]
    }

    Args:
        data: Dict or JSON string describing the document.
        output_path: Where to save the generated PDF.

    Returns:
        Path to the generated PDF.
    """
    if isinstance(data, str):
        data = json.loads(data)

    output_path = Path(output_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    body_style = styles["BodyText"]

    metadata_key_style = ParagraphStyle(
        "MetadataKey",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    story = []

    title = data.get("title")
    if title:
        story.append(Paragraph(str(title), title_style))
        story.append(Spacer(1, 0.5 * cm))

    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata:
        metadata_rows = []
        for key, value in metadata.items():
            metadata_rows.append(
                [
                    Paragraph(str(key), metadata_key_style),
                    Paragraph(str(value), body_style),
                ]
            )

        metadata_table = Table(metadata_rows, colWidths=[4 * cm, 11 * cm])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(metadata_table)
        story.append(Spacer(1, 0.7 * cm))

    sections = data.get("sections", [])

    for section in sections:
        heading = section.get("heading")
        if heading:
            story.append(Paragraph(str(heading), heading_style))
            story.append(Spacer(1, 0.25 * cm))

        content = section.get("content", [])

        for block in content:
            block_type = block.get("type")

            if block_type == "paragraph":
                text = block.get("text", "")
                story.append(Paragraph(str(text), body_style))
                story.append(Spacer(1, 0.3 * cm))

            elif block_type == "bullets":
                items = block.get("items", [])
                bullet_items = [
                    ListItem(Paragraph(str(item), body_style)) for item in items
                ]

                story.append(
                    ListFlowable(
                        bullet_items,
                        bulletType="bullet",
                        leftIndent=18,
                    )
                )
                story.append(Spacer(1, 0.3 * cm))

            elif block_type == "table":
                headers = block.get("headers", [])
                rows = block.get("rows", [])

                table_data = []

                if headers:
                    table_data.append(
                        [Paragraph(str(cell), body_style) for cell in headers]
                    )

                for row in rows:
                    table_data.append(
                        [Paragraph(str(cell), body_style) for cell in row]
                    )

                table = Table(table_data, repeatRows=1)

                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                story.append(table)
                story.append(Spacer(1, 0.4 * cm))

            else:
                # Fallback: render unknown blocks as JSON text
                story.append(Paragraph(str(block), body_style))
                story.append(Spacer(1, 0.3 * cm))

    doc.build(story)

    return output_path
