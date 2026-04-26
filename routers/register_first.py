# routers/register_first.py
"""
Creación del primer usuario administrador.
Solo accesible si la base de datos está vacía.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from db.users import has_any_user, create_user_admin

router = APIRouter()


@router.get("/register-first", response_class=HTMLResponse)
def register_first_form(request: Request):
    if has_any_user():
        return RedirectResponse("/login", status_code=303)

    return request.app.state.templates.TemplateResponse(
        "register_first.html",
        {
            "request": request,
            "logo_path": "/static/logo.png",
        },
    )


@router.post("/register-first")
def register_first_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
):
    if has_any_user():
        return RedirectResponse("/login", status_code=303)

    # Crear primer admin SIN contraseña
    create_user_admin(
        name=name.strip(),
        email=email.strip(),
        role="admin",
        created_by=None,
    )

    # Al ir a /login, se activará el flujo /first-login automáticamente
    return RedirectResponse("/login", status_code=303)
