# utils/pdf_ranking_groups.py
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Image,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def pdf_ranking_groups(
    rows: list[dict],
    titulo: str,
    logo_path: Path | None = None,
) -> bytes:
    """
    PDF Ranking de grupos.

    Columnas:
      Rank | Grupo | Incidencias
    """

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ==========================
    # ENCABEZADO
    # ==========================
    header_cells = []

    if logo_path and logo_path.exists():
        header_cells.append(Image(str(logo_path), width=50, height=50))
    else:
        header_cells.append("")

    header_cells.append(
        Paragraph(f"<b>{titulo}</b>", styles["Heading2"])
    )

    elements.append(
        Table(
            [header_cells],
            colWidths=[70, doc.width - 70],
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # TABLA
    # ==========================
    data = [
        ["Rank", "Grupo", "Incidencias"]
    ]

    for r in rows:
        data.append([
            r["rank"],
            r["grupo"],
            r["partes"],
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
