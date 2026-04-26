# routers/incidents_list.py
"""
Listado de incidencias.
Vista común con filtros automáticos y permisos por rol.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from datetime import date

from auth import load_user_dep
from context import ctx

from db.incidents import get_incidents
from db.students import get_all_groups, get_students_by_group
from db.users import get_all_teachers

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/incidents/list", response_class=HTMLResponse)
def incidents_list(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    role = user["role"]
    qp = request.query_params

    # --------------------------------------------------
    # Filtros (GET params)
    # --------------------------------------------------
    # fecha_desde = qp.get("fecha_desde") or INICIO_CURSO
    # fecha_hasta = qp.get("fecha_hasta") or date.today().isoformat()
    fecha_desde = qp.get("fecha_desde")
    fecha_hasta = qp.get("fecha_hasta")
    grupo = qp.get("grupo") or None
    alumno = qp.get("alumno") or None
    gravedad = qp.get("gravedad") or None

    # Solo relevante para roles de gestión
    profesor_id_raw = qp.get("profesor_id")
    profesor_id = int(profesor_id_raw) if profesor_id_raw else None

    # --------------------------------------------------
    # Decisión por rol + carga de incidencias
    # --------------------------------------------------
    if role in ("admin", "jefe", "director", "secretario", "convivencia"):
        incidents = get_incidents(
            mode="all",
            profesor_id=profesor_id,
            grupo=grupo,
            alumno=alumno,
            gravedad=gravedad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        show_profesor_filter = True

    elif role in ("profesor", "orientador"):
        incidents = get_incidents(
            mode="own",
            user_id=user["id"],
            grupo=grupo,
            alumno=alumno,
            gravedad=gravedad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        show_profesor_filter = False

    else:
        raise HTTPException(status_code=403)

    # --------------------------------------------------
    # Datos para desplegables de filtros
    # --------------------------------------------------
    grupos = get_all_groups()

    alumnos = get_students_by_group(grupo) if grupo else []

    profesores = get_all_teachers() if show_profesor_filter else []

    # --------------------------------------------------
    # Render
    # --------------------------------------------------
    return request.app.state.templates.TemplateResponse(
        "incidents/list.html",
        ctx(
            request,
            user=user,
            title="Listado de incidencias",
            incidents=incidents,
            filters={
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "grupo": grupo,
                "alumno": alumno,
                "gravedad": gravedad,
                "profesor_id": profesor_id if show_profesor_filter else None,
            },
            show_profesor_filter=show_profesor_filter,
            grupos=grupos,
            alumnos=alumnos,
            profesores=profesores,
        ),
    )
