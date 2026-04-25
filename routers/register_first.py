# routers/register_first.py
"""
Creación del primer usuario administrador.
Solo accesible si la base de datos está vacía.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from db.users import count_users, create_user
from security.passwords import hash_password

router = APIRouter()


@router.get("/register-first", response_class=HTMLResponse)
def register_first_form(request: Request):
    """
    Muestra el formulario de creación del primer admin.
    """
    if count_users() > 0:
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
    password: str = Form(...),
):
    """
    Crea el primer administrador.
    """
    if count_users() > 0:
        return RedirectResponse("/login", status_code=303)

    create_user(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )

    return RedirectResponse("/login", status_code=303)
