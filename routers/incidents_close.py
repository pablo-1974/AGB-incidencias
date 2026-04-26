# routers/incidents_close.py
"""
FASE 3 · Cierre de incidencias
Vista de gestión (solo ADMIN y JEFE)
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import load_user_dep
from context import ctx
from db.incidents import (
    get_open_incidents_for_closing,
    close_incident,
)
from utils.enums import GRAVEDADES

router = APIRouter()


# ------------------------------------------------------
# PERMISOS
# ------------------------------------------------------

def _can_close(user: dict):
    if user["role"] not in ("admin", "jefe"):
        raise HTTPException(status_code=403)


# ------------------------------------------------------
# VISTA · COLA DE INCIDENCIAS ABIERTAS
# ------------------------------------------------------

@router.get("/incidents/close", response_class=HTMLResponse)
def incidents_close_view(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    _can_close(user)

    incidents = get_open_incidents_for_closing()

    return request.app.state.templates.TemplateResponse(
        "incidents/close.html",
        ctx(
            request,
            user=user,
            title="Cerrar incidencias",
            incidents=incidents,
            gravedades=GRAVEDADES,
        ),
    )


# ------------------------------------------------------
# ACCIÓN · CERRAR INCIDENCIA
# ------------------------------------------------------

@router.post("/incidents/close/{incident_id}")
def incidents_close_submit(
    incident_id: int,
    request: Request,
    user: dict = Depends(load_user_dep),
    gravedad_final: str = Form(...),
):
    _can_close(user)

    if gravedad_final not in GRAVEDADES:
        return Redirect
