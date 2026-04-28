# routers/incidents_create.py
"""
Creación de incidencias.

Formulario genérico para registrar una nueva incidencia.
Reutiliza la lógica de la aplicación anterior (sin Streamlit).
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import load_user_dep
from context import ctx
from datetime import date, datetime

from db.students import get_all_groups, get_students_by_group
from db.incidents import create_incident
from utils.enums import GRAVEDADES, FRANJAS_HORARIAS, FRANJA_ORDEN
from utils.permissions import has_permission
from utils.enums import PERM_ABRIR_INCIDENCIA

router = APIRouter()


# ----------------------------------------------------------------------
# FORMULARIO (GET)
# ----------------------------------------------------------------------

@router.get("/incidents/create", response_class=HTMLResponse)
def incident_create_form(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    if not has_permission(user, PERM_ABRIR_INCIDENCIA):
        raise HTTPException(status_code=403)
        
    grupos = get_all_groups()

    return request.app.state.templates.TemplateResponse(
        "incidents/create.html",
        ctx(
            request,
            user=user,
            title="Abrir incidencia",
            grupos=grupos,
            gravedades=GRAVEDADES,
            franjas=FRANJAS_HORARIAS,
            today=date.today().isoformat(),
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
    hora: str = Form(...),
    gravedad: str = Form(...),
    descripcion: str = Form(...),
):
    if not has_permission(user, PERM_ABRIR_INCIDENCIA):
        raise HTTPException(status_code=403)
        
    # ---------------------------
    # Validación de grupo
    # ---------------------------
    if not grupo:
        return RedirectResponse("/incidents/create?error=grupo", status_code=303)

    # ---------------------------
    # Validación de alumno
    # ---------------------------
    if not alumno:
        return RedirectResponse("/incidents/create?error=alumno", status_code=303)

    # ---------------------------
    # ✅ VALIDACIÓN DE FECHA (AQUÍ)
    # ---------------------------
    if not fecha:
        return RedirectResponse("/incidents/create?error=fecha", status_code=303)

    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return RedirectResponse("/incidents/create?error=fecha", status_code=303)

    # ---------------------------
    # Validación de franja
    # ---------------------------
    if hora not in FRANJAS_HORARIAS:
        return RedirectResponse("/incidents/create?error=hora", status_code=303)
        
    # ---------------------------
    # Validación de gravedad
    # ---------------------------
    if gravedad not in GRAVEDADES:
        return RedirectResponse("/incidents/create?error=gravedad", status_code=303)

    # ---------------------------
    # Validación de descripción
    # ---------------------------
    if not descripcion.strip():
        return RedirectResponse("/incidents/create?error=descripcion", status_code=303)

    # ---------------------------
    # Crear incidencia
    # ---------------------------
    create_incident(
        user_id=user["id"],
        user_name=user["name"],
        grupo=grupo,
        alumno=alumno,
        fecha=fecha,
        hora=hora,
        hora_orden=FRANJA_ORDEN[hora],
        descripcion=descripcion.strip(),
        gravedad=gravedad,
    )

    return RedirectResponse("/", status_code=303)

# ----------------------------------------------------------------------
# GRUPO (GET)
# ----------------------------------------------------------------------

@router.get("/incidents/students/{grupo}")
def get_students_for_group(
    grupo: str,
    user: dict = Depends(load_user_dep),
):
    return get_students_by_group(grupo)
