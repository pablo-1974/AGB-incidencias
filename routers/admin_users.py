# routers/admin_users.py
"""
Gestión de usuarios (ADMIN).
Listado, creación, edición, activación y reset de contraseña.
Acceso exclusivo para el rol admin.
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
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

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
    Crea un usuario nuevo (sin contraseña).
    Fuerza primer login.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    if role not in ROLES_TODOS:
        raise HTTPException(status_code=400, detail="Rol no válido")

    create_user_admin(
        name=name.strip(),
        email=email.strip(),
        role=role,
        created_by=user["id"],
    )

    return RedirectResponse("/admin/users", status_code=303)


# ----------------------------------------------------------------------
# EDITAR USUARIO (nombre / email / rol)
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
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    if role not in ROLES_TODOS:
        raise HTTPException(status_code=400, detail="Rol no válido")

    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404)

    update_user_admin(
        user_id=user_id,
        name=name.strip(),
        email=email.strip(),
        role=role,
    )

    return RedirectResponse("/admin/users", status_code=303)


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
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404)

    set_user_active(
        user_id=user_id,
        active=not bool(target["active"]),
    )

    return RedirectResponse("/admin/users", status_code=303)


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
    Fuerza primer login.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404)

    reset_user_password(user_id=user_id)

    return RedirectResponse("/admin/users", status_code=303)
