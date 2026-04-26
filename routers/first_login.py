# routers/first_login.py
"""
Flujo de primer login / reset de contraseña.
Obliga a definir contraseña antes de acceder a la aplicación.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from context import ctx
from db.users import get_user_by_id, set_user_password
from security.passwords import hash_password

router = APIRouter()


@router.get("/first-login", response_class=HTMLResponse)
def first_login_form(request: Request):
    """
    Muestra el formulario de definición de contraseña.
    """
    user_id = request.session.get("first_login_user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = get_user_by_id(user_id)

    if not user or user["active"] != 1:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    return request.app.state.templates.TemplateResponse(
        "first_login.html",
        ctx(
            request,
            user=None,
            title="Definir contraseña",
            hide_chrome=True,
        ),
    )


@router.post("/first-login", response_class=HTMLResponse)
def first_login_submit(
    request: Request,
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    """
    Guarda la contraseña y activa el usuario.
    """
    user_id = request.session.get("first_login_user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = get_user_by_id(user_id)

    if not user or user["active"] != 1:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    # Validaciones básicas
    if password != password_confirm:
        return request.app.state.templates.TemplateResponse(
            "first_login.html",
            ctx(
                request,
                user=None,
                title="Definir contraseña",
                hide_chrome=True,
                error="Las contraseñas no coinciden.",
            ),
        )

    if len(password) < 8:
        return request.app.state.templates.TemplateResponse(
            "first_login.html",
            ctx(
                request,
                user=None,
                title="Definir contraseña",
                hide_chrome=True,
                error="La contraseña debe tener al menos 8 caracteres.",
            ),
        )

    # Actualizar contraseña en BD
    password_hash = hash_password(password)
    set_user_password(
        user_id=user_id,
        password_hash=password_hash,
    )

    # Limpiar sesión temporal y crear sesión normal
    request.session.clear()
    request.session["user_id"] = user_id

    return RedirectResponse("/dashboard", status_code=303)
