# routers/analysis_teacher_pdf.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path

from db.incidents import get_incidents
from auth import load_user_dep
from utils.pdf_teacher_history import pdf_teacher_history

router = APIRouter()


@router.get("/analysis/teacher/pdf")
def analysis_teacher_pdf(
    request: Request,
    profesor: str,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    PDF: Historial de incidencias por profesor.
    """

    # ---------------------------------
    # 1. Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        profesor=profesor,
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
            alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            _profesor,
        ) = r

        rows.append({
            "fecha": fecha,
            "hora": hora or "",
            "alumno": alumno,
            "grupo": grupo,
            "gravedad": grav_fin or grav_ini,
            "descripcion": descripcion,
        })

    # ---------------------------------
    # 3. Generar PDF
    # ---------------------------------
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_teacher_history(
            rows=rows,
            profesor=profesor,
            fecha_desde=from_,
            fecha_hasta=to,
            logo_path=Path("static/logo.png"),
            output_path=tmp.name,
        )

        return FileResponse(
            tmp.name,
            filename=f"historial_profesor_{profesor.replace(' ', '_')}.pdf",
            media_type="application/pdf",
        )
