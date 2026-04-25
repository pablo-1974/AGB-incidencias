# routers/analysis_student_pdf.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path

from db.incidents import get_incidents
from auth import load_user_dep
from utils.pdf_student_history import pdf_student_history

router = APIRouter()


@router.get("/analysis/student/pdf")
def analysis_student_pdf(
    request: Request,
    alumno: str,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    PDF: Historial de incidencias por alumno.
    """

    # ---------------------------------
    # 1. Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        alumno=alumno,
        fecha_desde=from_,
        fecha_hasta=to,
    )

    if not rows_raw:
        return FileResponse(
            path=None,
            media_type="text/plain",
            status_code=404,
            filename="sin_datos.txt",
        )

    # ---------------------------------
    # 2. Preparar datos PDF
    # ---------------------------------
    rows = []

    for r in rows_raw:
        (
            _id,
            fecha,
            hora,
            grupo,
            _alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            profesor,
        ) = r

        rows.append({
            "fecha": fecha,
            "hora": hora or "",
            "profesor": profesor,
            "gravedad": grav_fin or grav_ini,
            "descripcion": descripcion,
        })

    grupo_alumno = rows_raw[0][3]

    # ---------------------------------
    # 3. Generar PDF
    # ---------------------------------
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_student_history(
            rows=rows,
            alumno=alumno,
            grupo=grupo_alumno,
            fecha_desde=from_,
            fecha_hasta=to,
            logo_path=Path("static/logo.png"),
            output_path=tmp.name,
        )

        return FileResponse(
            tmp.name,
            filename=f"historial_{alumno.replace(' ', '_')}.pdf",
            media_type="application/pdf",
        )
