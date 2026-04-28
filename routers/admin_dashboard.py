# routers/admin_dashboard.py
"""
Dashboard principal del administrador.

Muestra:
- Aviso principal del sistema: incidencias abiertas

Acceso exclusivo para el rol admin.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse

from auth import load_user_dep
from context import ctx
from db.incidents import (
    count_open_incidents,
    count_total_incidents,
)

router = APIRouter()


# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------

def _require_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403)


# ----------------------------------------------------------------------
# DASHBOARD ADMIN
# ----------------------------------------------------------------------

@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    """
    Dashboard principal del administrador.
    """
    _require_admin(user)

    # KPI PRINCIPAL
    open_incidences = count_open_incidents()
    total_incidences = count_total_incidents()


    return request.app.state.templates.TemplateResponse(
        "admin/dashboard.html",
        ctx(
            request,
            user=user,
            title="Dashboard de administración",
            kpis={
                "open_incidences": open_incidences,
                "total_incidences": total_incidences,
            },
        ),
    )
