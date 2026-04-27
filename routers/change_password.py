# routers/change_password.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import load_user_dep, verify_password, hash_password
from context import ctx
from db.users import update_user_password

router = APIRouter()


# ------------------------------------------------------
# VISTA · FORMULARIO CAMBIO DE CONTRASEÑA
# ------------------------------------------------------

@router.get("/change-password", response_class=HTMLResponse)
def change_password_view(
    request: Request,
    user=Depends(load_user_dep),
):
    """
    Muestra el formulario de cambio de contraseña.
    Requiere usuario autenticado.
    """
    return request.app.state.templates.TemplateResponse(
        "auth/change_password.html",
        ctx(
            request,
            user,
            title="Cambiar contraseña",
        ),
    )


# ------------------------------------------------------
# ACCIÓN · CAMBIAR CONTRASEÑA
# ------------------------------------------------------

@router.post("/change-password")
def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user=Depends(load_user_dep),
):
    """
    Procesa el cambio de contraseña.
    """

    # 1️⃣ Comprobar contraseña actual
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual no es correcta",
        )

    # 2️⃣ Validar nueva contraseña
    if new_password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña y su confirmación no coinciden",
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe tener al menos 6 caracteres",
        )

    # 3️⃣ Hashear y guardar
    new_hash = hash_password(new_password)

    update_user_password(
        user_id=user["id"],
        password_hash=new_hash,
    )

    # 4️⃣ Redirección final
    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303,
    )
