# routers/analysis_student_pdf.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import date

from db.incidents import get_incidents
from auth import load_user_dep
from utils.pdf_student_history import pdf_student_history

router = APIRouter()


@router.get("/analysis/student/pdf")
def analysis_student_pdf(
    request: Request,
    grupo: str | None = None,
    alumno: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    PDF: Historial de incidencias.
    - Global
    - Por grupo
    - Por alumno
    """

    # ---------------------------------
    # 1. Fechas por defecto (seguridad)
    # ---------------------------------
    fecha_desde = from_ or "2025-09-01"
    fecha_hasta = to or date.today().isoformat()

    # ---------------------------------
    # 2. Cargar incidencias según filtros
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        grupo=grupo,
        alumno=alumno,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    if not rows_raw:
        raise HTTPException(
            status_code=404,
            detail="No hay incidencias para los filtros seleccionados",
        )

    # ---------------------------------
    # 3. Preparar filas para el PDF
    # ---------------------------------
    rows = []

    for r in rows_raw:
        rows.append({
            "fecha": r["fecha"],
            "hora": r["franja"] or "",
            "profesor": r["teacher_name"],
            "gravedad": r["gravedad_final"] or r["gravedad_inicial"],
            "descripcion": r["descripcion"],
            "grupo": r["grupo"],
            "alumno": r["alumno"],
        })

    # ---------------------------------
    # 4. Título del PDF (según filtros)
    # ---------------------------------
    if alumno:
        titulo = f"Historial de incidencias del alumno {alumno}"
    elif grupo:
        titulo = f"Historial de incidencias del grupo {grupo}"
    else:
        titulo = "Historial de incidencias de alumnos"

    # ---------------------------------
    # 5. Generar PDF
    # ---------------------------------
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_student_history(
            rows=rows,
            titulo=titulo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            logo_path=Path("static/logo.png"),
            output_path=tmp.name,
        )

        return FileResponse(
            tmp.name,
            filename="historial_incidencias.pdf",
            media_type="application/pdf",
        )
