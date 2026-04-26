# routers/admin_incidents.py
"""
Listado de incidencias (ADMIN).

Vista global de todas las incidencias del sistema.
Acceso exclusivo para el rol admin.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse

from auth import load_user_dep
from context import ctx
from db.incidents import get_incidents

router = APIRouter()


# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------

def _require_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403)


# ----------------------------------------------------------------------
# LISTADO DE INCIDENCIAS
# ----------------------------------------------------------------------

@router.get("/admin/incidents", response_class=HTMLResponse)
def admin_incidents_list(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    _require_admin(user)

    incidents = get_incidents(mode="all")

    return request.app.state.templates.TemplateResponse(
        "admin/incidents_list.html",
        ctx(
            request,
            user=user,
            title="Listado de incidencias",
            incidents=incidents,
        ),
    )
