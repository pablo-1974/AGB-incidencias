# routers/admin_users.py
"""
Gestión de usuarios (ADMIN).

Funcionalidades:
- Listar usuarios
- Crear usuario (sin contraseña → primer login)
- Editar nombre, email y rol
- Activar / desactivar usuario
- Resetear contraseña (forzar primer login)

Acceso exclusivo para el rol admin.
Incluye salvaguardas para evitar dejar el sistema sin administradores.
"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from context import ctx
from auth import load_user_dep
from utils.enums import ROLES_TODOS
from db.users import (
    get_all_users,
    get_user_by_id,
    create_user_admin,
    update_user_admin,
    set_user_active,
    reset_user_password,
)

router = APIRouter()


# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------

def _count_active_admins() -> int:
    """
    Devuelve el número de administradores activos.
    """
    from db.connection import get_db

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE role = 'admin'
                  AND active = 1
                """
            )
            return cur.fetchone()[0]


def _require_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403)


# ----------------------------------------------------------------------
# LISTADO DE USUARIOS
# ----------------------------------------------------------------------

@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    user=load_user_dep,
):
    """
    Pantalla principal de gestión de usuarios.
    """
    _require_admin(user)

    users = get_all_users()

    return request.app.state.templates.TemplateResponse(
        "admin/users.html",
        ctx(
            request,
            user=user,
            title="Gestión de usuarios",
            users=users,
        ),
    )


# ----------------------------------------------------------------------
# CREAR USUARIO
# ----------------------------------------------------------------------

@router.post("/admin/users/create")
def admin_users_create(
    request: Request,
    user=load_user_dep,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
):
    """
    Crea un usuario nuevo sin contraseña.
    El usuario deberá definirla en su primer acceso.
    """
    _require_admin(user)

    if role not in ROLES_TODOS:
        return RedirectResponse("/admin/users?status=error", status_code=303)

    create_user_admin(
        name=name.strip(),
        email=email.strip(),
        role=role,
        created_by=user["id"],
    )

    return RedirectResponse("/admin/users?status=created", status_code=303)


# ----------------------------------------------------------------------
# EDITAR USUARIO (NOMBRE / EMAIL / ROL)
# ----------------------------------------------------------------------

@router.post("/admin/users/update/{user_id}")
def admin_users_update(
    request: Request,
    user_id: int,
    user=load_user_dep,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
):
    """
    Actualiza nombre, email y rol de un usuario.
    """
    _require_admin(user)

    if role not in ROLES_TODOS:
        return RedirectResponse("/admin/users?status=error", status_code=303)

    target = get_user_by_id(user_id)
    if not target:
        return RedirectResponse("/admin/users?status=error", status_code=303)

    # Evitar quitar el último admin
    if target["role"] == "admin" and role != "admin":
        if _count_active_admins() <= 1:
            return RedirectResponse("/admin/users?status=error", status_code=303)

    update_user_admin(
        user_id=user_id,
        name=name.strip(),
        email=email.strip(),
        role=role,
    )

    return RedirectResponse("/admin/users?status=updated", status_code=303)


# ----------------------------------------------------------------------
# ACTIVAR / DESACTIVAR USUARIO
# ----------------------------------------------------------------------

@router.post("/admin/users/toggle/{user_id}")
def admin_users_toggle(
    request: Request,
    user_id: int,
    user=load_user_dep,
):
    """
    Activa o desactiva un usuario.
    """
    _require_admin(user)

    target = get_user_by_id(user_id)
    if not target:
        return RedirectResponse("/admin/users?status=error", status_code=303)

    # Evitar desactivar el último admin activo
    if target["role"] == "admin" and target["active"] == 1:
        if _count_active_admins() <= 1:
            return RedirectResponse("/admin/users?status=error", status_code=303)

    set_user_active(
        user_id=user_id,
        active=not bool(target["active"]),
    )

    return RedirectResponse("/admin/users?status=toggled", status_code=303)


# ----------------------------------------------------------------------
# RESET DE CONTRASEÑA
# ----------------------------------------------------------------------

@router.post("/admin/users/reset-password/{user_id}")
def admin_users_reset_password(
    request: Request,
    user_id: int,
    user=load_user_dep,
):
    """
    Resetea la contraseña de un usuario.
    Fuerza el flujo de primer login.
    """
    _require_admin(user)

    target = get_user_by_id(user_id)
    if not target:
        return RedirectResponse("/admin/users?status=error", status_code=303)

    reset_user_password(user_id=user_id)

    return RedirectResponse("/admin/users?status=reset", status_code=303)
