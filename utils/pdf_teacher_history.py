# utils/pdf_teacher_history.py
from io import BytesIO
from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet


def pdf_teacher_history(
    *,
    rows: list[dict],
    profesor: str,
    fecha_desde: date,
    fecha_hasta: date,
    logo_path: Path | None = None,
) -> bytes:
    """
    PDF DURO – Historial de profesor.

    Columnas:
      Nº | Fecha | Hora/Franja | Alumno | Grupo | Gravedad | Descripción
    """

    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    style_title = styles["Heading2"]
    style_cell = styles["BodyText"]
    style_cell.fontSize = 9
    style_cell.leading = 11

    elements = []

    # ==========================
    # ENCABEZADO
    # ==========================
    header_cells = []

    if logo_path and logo_path.exists():
        header_cells.append(Image(str(logo_path), width=60, height=60))
    else:
        header_cells.append("")

    title_txt = (
        f"<b>Historial de incidencias del profesor</b><br/>"
        f"{profesor}<br/>"
        f"<font size=9>"
        f"Periodo: {fecha_desde.strftime('%d/%m/%Y')} – {fecha_hasta.strftime('%d/%m/%Y')}"
        f"</font>"
    )

    header_cells.append(Paragraph(title_txt, style_title))

    header = Table(
        [header_cells],
        colWidths=[70, doc.width - 70],
    )
    elements.append(header)
    elements.append(Spacer(1, 14))

    # ==========================
    # TABLA PRINCIPAL
    # ==========================
    data = [
        [
            Paragraph("<b>Nº</b>", styles["Heading4"]),
            Paragraph("<b>Fecha</b>", styles["Heading4"]),
            Paragraph("<b>Hora / Franja</b>", styles["Heading4"]),
            Paragraph("<b>Alumno</b>", styles["Heading4"]),
            Paragraph("<b>Grupo</b>", styles["Heading4"]),
            Paragraph("<b>Gravedad</b>", styles["Heading4"]),
            Paragraph("<b>Descripción</b>", styles["Heading4"]),
        ]
    ]

    for i, r in enumerate(rows, start=1):
        data.append([
            Paragraph(str(i), style_cell),
            Paragraph(r["fecha"], style_cell),
            Paragraph(r["hora"] or "", style_cell),
            Paragraph(r["alumno"], style_cell),
            Paragraph(r["grupo"], style_cell),
            Paragraph(r["gravedad"], style_cell),
            Paragraph(r["descripcion"], style_cell),
        ])

    table = Table(
        data,
        colWidths=[
            36,   # Nº
            70,   # Fecha
            70,   # Hora / Franja
            140,  # Alumno
            70,   # Grupo
            70,   # Gravedad
            344,  # Descripción (muy ancha)
        ],
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)

    doc.build(elements)
    return buf.getvalue()
