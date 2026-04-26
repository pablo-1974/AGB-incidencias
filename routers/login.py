# routers/login.py
"""
Login y logout de la aplicación.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from context import ctx
from db.users import get_user_by_email
from security.passwords import verify_password

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    """
    Muestra el formulario de login.
    """
    return request.app.state.templates.TemplateResponse(
        "login.html",
        ctx(
            request,
            user=None,
            title="Acceso",
            hide_chrome=True,
        ),
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Procesa el login.
    """
    user = get_user_by_email(email)

    # Usuario inexistente
    if not user:
        return request.app.state.templates.TemplateResponse(
            "login.html",
            ctx(
                request,
                user=None,
                title="Acceso",
                hide_chrome=True,
                error="Credenciales incorrectas",
                email=email,
            ),
        )

    # Usuario desactivado
    if user["active"] != 1:
        return request.app.state.templates.TemplateResponse(
            "login.html",
            ctx(
                request,
                user=None,
                title="Acceso",
                hide_chrome=True,
                error="El usuario está desactivado. Contacta con un administrador.",
                email=email,
            ),
        )

    # Primer login o reset de contraseña
    if user["password_hash"] is None or user.get("must_change_password"):
        # Guardamos usuario en sesión temporal
        request.session.clear()
        request.session["first_login_user_id"] = user["id"]

        return RedirectResponse(
            url="/first-login",
            status_code=303,
        )

    # Validación de contraseña normal
    if not verify_password(password, user["password_hash"]):
        return request.app.state.templates.TemplateResponse(
            "login.html",
            ctx(
                request,
                user=None,
                title="Acceso",
                hide_chrome=True,
                error="Credenciales incorrectas",
                email=email,
            ),
        )

    # Login correcto → sesión normal
    request.session.clear()
    request.session["user_id"] = user["id"]

    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    """
    Cierra la sesión.
    """
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
