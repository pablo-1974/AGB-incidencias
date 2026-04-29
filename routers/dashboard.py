# routers/dashboard.py

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from auth import load_user_dep

router = APIRouter()


@router.get("/dashboard")
def dashboard_entry(user: dict = Depends(load_user_dep)):
    """
    Punto de entrada general al dashboard.
    Redirige según rol/permisos.
    """

    # Administrador y Jefe → dashboard común
    if user["role"] in ("admin", "jefe"):
        return RedirectResponse("/admin/dashboard", status_code=303)

    # Profesor / orientador (ejemplo)
    if user["role"] in ("profesor", "orientador"):
        return RedirectResponse("/incidents/list", status_code=303)

    # Fallback seguro
    return RedirectResponse("/login", status_code=303)
