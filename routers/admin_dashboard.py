# routers/admin_dashboard.py
"""
Dashboard principal del administrador.

Muestra:
- KPIs globales del sistema (usuarios)
- Accesos rápidos a funciones administrativas
- Resumen operativo: últimos usuarios creados

Acceso exclusivo para el rol admin.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from auth import load_user_dep
from context import ctx
from db.users import get_all_users

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
    user=load_user_dep,
):
    """
    Dashboard principal del administrador.
    """
    _require_admin(user)

    users = get_all_users()

    total_users = len(users)
    active_users = sum(1 for u in users if u["active"] == 1)
    inactive_users = total_users - active_users
    pending_first_login = sum(
        1 for u in users
        if u["must_change_password"] or not u["password_hash"]
    )

    # Últimos usuarios creados (máx 10)
    last_users = sorted(
        users,
        key=lambda u: u["created_at"],
        reverse=True
    )[:10]

    return request.app.state.templates.TemplateResponse(
        "admin/dashboard.html",
        ctx(
            request,
            user=user,
            title="Dashboard de administración",
            kpis={
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "pending_first_login": pending_first_login,
            },
            last_users=last_users,
        ),
    )
