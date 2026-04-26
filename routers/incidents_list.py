# routers/incidents.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from datetime import date

from auth import load_user_dep
from context import ctx
from db.incidents import get_incidents

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/incidents/list", response_class=HTMLResponse)
def incidents_list(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    role = user["role"]
    qp = request.query_params

    # ---------------------------
    # Filtros (GET params)
    # ---------------------------
    fecha_desde = qp.get("fecha_desde") or INICIO_CURSO
    fecha_hasta = qp.get("fecha_hasta") or date.today().isoformat()
    grupo = qp.get("grupo") or None
    alumno = qp.get("alumno") or None
    gravedad = qp.get("gravedad") or None

    # Solo para roles de gestión
    profesor_id = qp.get("profesor_id")

    # ---------------------------
    # Decisión por rol
    # ---------------------------
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

    # ---------------------------
    # Render
    # ---------------------------
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
                "profesor_id": profesor_id if show_profesor_filter else None,
                "gravedad": gravedad,
            },
            show_profesor_filter=show_profesor_filter,
        ),
    )
