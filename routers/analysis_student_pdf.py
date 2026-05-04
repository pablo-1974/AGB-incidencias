# routers/analysis_student_pdf.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response
from datetime import date
from pathlib import Path

from auth import load_user_dep
from db.incidents import get_incidents
from utils.pdf_student_history import pdf_student_history

from utils.permissions import has_permission
from utils.enums import PERM_HISTORIAL_ALUMNO

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
    PDF de historial de incidencias:

    - Sin filtros → PDF general (con grupo y alumno)
    - Con grupo    → PDF del grupo (con grupo y alumno)
    - Con alumno   → PDF del alumno (sin grupo ni alumno en columnas)
    """
    
    # ✅ CONTROL DE PERMISOS (PASO 5)
    if not has_permission(user, PERM_HISTORIAL_ALUMNO):
        raise HTTPException(status_code=403)

    # --------------------------------------------------
    # 1. Fechas por defecto
    # --------------------------------------------------
    fecha_desde = from_ or "2025-09-01"
    fecha_hasta = to or date.today().isoformat()

    # --------------------------------------------------
    # 2. Cargar incidencias
    # --------------------------------------------------
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

    # ✅ Invertir orden para PDF (N → 1)
    rows_raw = list(reversed(rows_raw))

    # --------------------------------------------------
    # 3. Preparar filas (SIEMPRE con grupo y alumno)
    #    El PDF decidirá qué columnas mostrar
    # --------------------------------------------------
    rows = []

    for r in rows_raw:
        rows.append({
            "fecha": r["fecha"],
            "hora": r["franja"] or "",
            "grupo": r["grupo"],
            "alumno": r["alumno"],
            "profesor": r["teacher_name"],
            "gravedad": r["gravedad_final"] or r["gravedad_inicial"],
            "descripcion": r["descripcion"],
        })

    # --------------------------------------------------
    # 4. Decidir modo y título del PDF
    # --------------------------------------------------
    if alumno:
        modo = "alumno"
        titulo = f"Historial de incidencias del alumno {alumno}"
    elif grupo:
        modo = "general"
        titulo = f"Historial de incidencias del grupo {grupo}"
    else:
        modo = "general"
        titulo = "Historial de incidencias de alumnos"

    # --------------------------------------------------
    # 5. Generar PDF (devuelve BYTES)
    # --------------------------------------------------
    pdf_bytes = pdf_student_history(
        rows=rows,
        titulo=titulo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        logo_path=Path("static/logo.png"),
        modo=modo,   # 👈 AQUÍ está la clave
    )

    # --------------------------------------------------
    # 6. Devolver PDF correctamente
    # --------------------------------------------------
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=historial_incidencias.pdf"
        },
    )
