# utils/pdf_ranking_students.py
from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def pdf_ranking_students(
    rows: list[dict],
    titulo: str,
    logo_path: Path | None = None,
) -> bytes:

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36)

    styles = getSampleStyleSheet()
    elements = []

    # Encabezado
    head = []
    if logo_path and logo_path.exists():
        head.append(Image(str(logo_path), width=50, height=50))
    else:
        head.append("")

    head.append(Paragraph(f"<b>{titulo}</b>", styles["Heading2"]))

    elements.append(Table([head], colWidths=[70, doc.width - 70]))
    elements.append(Spacer(1, 12))

    # Tabla
    data = [[
        "Rank", "Grupo", "Alumno", "Incidencias", "Puntos"
    ]]

    for r in rows:
        data.append([
            r["rank"],
            r["grupo"],
            r["alumno"],
            r["partes"],
            r.get("puntos", ""),
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (3,1), (-1,-1), "RIGHT"),
    ]))

    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
