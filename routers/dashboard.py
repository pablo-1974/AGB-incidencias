# routers/dashboard.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from context import ctx
from auth import load_user_dep

router = APIRouter(prefix="/dashboard")


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user=Depends(load_user_dep),
):
    """
    Dashboard principal de Incidencias.
    """
    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        ctx(
            request,
            user,
            title="Panel de control",
        ),
    )
