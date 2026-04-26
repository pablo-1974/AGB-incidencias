# routers/incidents_create.py
"""
Creación de incidencias.

Formulario genérico para registrar una nueva incidencia.
Reutiliza la lógica de la aplicación anterior (sin Streamlit).
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import load_user_dep
from context import ctx

from db.students import get_all_groups, get_students_by_group
from db.incidents import create_incident
from utils.enums import GRAVEDADES

router = APIRouter()


# ----------------------------------------------------------------------
# FORMULARIO (GET)
# ----------------------------------------------------------------------

@router.get("/incidents/create", response_class=HTMLResponse)
def incident_create_form(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    grupos = get_all_groups()

    return request.app.state.templates.TemplateResponse(
        "incidents/create.html",
        ctx(
            request,
            user=user,
            title="Crear incidencia",
            grupos=grupos,
            gravedades=GRAVEDADES,
        ),
    )


# ----------------------------------------------------------------------
# ENVÍO (POST)
# ----------------------------------------------------------------------

@router.post("/incidents/create")
def incident_create_submit(
    request: Request,
    user: dict = Depends(load_user_dep),
    grupo: str = Form(...),
    alumno: str = Form(...),
    fecha: str = Form(...),
    gravedad: str = Form(...),
    descripcion: str = Form(...),
):
    # VALIDACIONES (idénticas a Streamlit)
    if not grupo or grupo.startswith("—"):
        return RedirectResponse("/incidents/create?error=grupo", status_code=303)

    if not alumno or alumno.startswith("—"):
        return RedirectResponse("/incidents/create?error=alumno", status_code=303)

    if gravedad not in GRAVEDADES:
        return RedirectResponse("/incidents/create?error=gravedad", status_code=303)

    if not descripcion.strip():
        return RedirectResponse("/incidents/create?error=descripcion", status_code=303)

    # CREACIÓN EN BD
    create_incident(
        user_id=user["id"],
        user_name=user["name"],
        grupo=grupo,
        alumno=alumno,
        fecha=fecha,
        descripcion=descripcion.strip(),
        gravedad=gravedad,
    )

    return RedirectResponse("/admin/dashboard", status_code=303)
