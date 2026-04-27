# routers/analysis_teacher_pdf.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response
from datetime import date
from pathlib import Path

from auth import load_user_dep
from db.incidents import get_incidents
from utils.pdf_teacher_history import pdf_teacher_history

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/analysis/teacher/pdf")
def analysis_teacher_pdf(
    request: Request,
    profesor: str | None = None,
    grupo: str | None = None,
    alumno: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    PDF de historial de incidencias por profesor.

    - Sin profesor → PDF general
    - Con profesor → PDF del profesor
    """

    # --------------------------------------------------
    # 1. Fechas por defecto
    # --------------------------------------------------
    fecha_desde = from_ or INICIO_CURSO
    fecha_hasta = to or date.today().isoformat()

    # --------------------------------------------------
    # 2. Cargar incidencias
    # --------------------------------------------------
    rows_raw = get_incidents(
        mode="all",
        profesor=profesor,
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

    # --------------------------------------------------
    # 3. Preparar filas (NO incluimos profesor en filas)
    # --------------------------------------------------
    rows = []

    for r in rows_raw:
        rows.append({
            "fecha": r["fecha"],
            "hora": r["franja"] or "",
            "grupo": r["grupo"],
            "alumno": r["alumno"],
            "gravedad": r["gravedad_final"] or r["gravedad_inicial"],
            "descripcion": r["descripcion"],
        })

    # --------------------------------------------------
    # 4. Título del PDF
    # --------------------------------------------------
    if profesor:
        titulo = f"Historial de incidencias del profesor {profesor}"
    else:
        titulo = "Historial de incidencias por profesor"

    # --------------------------------------------------
    # 5. Generar PDF (devuelve BYTES)
    # --------------------------------------------------
    pdf_bytes = pdf_teacher_history(
        rows=rows,
        titulo=titulo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        logo_path=Path("static/logo.png"),
    )

    # --------------------------------------------------
    # 6. Respuesta correcta
    # --------------------------------------------------
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=historial_profesor.pdf"
        },
    )
