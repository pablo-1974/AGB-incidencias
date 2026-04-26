# routers/admin_incidents_close.py
"""
Cierre de incidencias (ADMIN / Jefatura).

Cola de incidencias abiertas priorizada por gravedad y antigüedad.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import load_user_dep
from context import ctx
from db.connection import get_db
from db.incidents import close_incident
from utils.enums import GRAVEDADES, GRAVEDAD_MUY_GRAVE, GRAVEDAD_GRAVE

router = APIRouter()


# ----------------------------------------------------------------------
# UTILIDAD
# ----------------------------------------------------------------------

def _require_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403)


# ----------------------------------------------------------------------
# CARGA DE INCIDENCIAS ABIERTAS
# ----------------------------------------------------------------------

def _load_pending_incidents():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    fecha,
                    grupo,
                    alumno,
                    descripcion,
                    gravedad_inicial,
                    teacher_name
                FROM incidents
                WHERE estado != 'cerrado'
                ORDER BY
                    CASE gravedad_inicial
                        WHEN %s THEN 1
                        WHEN %s THEN 2
                        ELSE 3
                    END,
                    fecha ASC,
                    id ASC
                """,
                (GRAVEDAD_MUY_GRAVE, GRAVEDAD_GRAVE),
            )
            return cur.fetchall()


# ----------------------------------------------------------------------
# VISTA (GET)
# ----------------------------------------------------------------------

@router.get("/admin/incidents/close", response_class=HTMLResponse)
def incidents_close_view(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    _require_admin(user)

    incidents = _load_pending_incidents()

    return request.app.state.templates.TemplateResponse(
        "admin/incidents_close.html",
        ctx(
            request,
            user=user,
            title="Cerrar incidencias",
            incidents=incidents,
            gravedades=GRAVEDADES,
        ),
    )


# ----------------------------------------------------------------------
# CIERRE (POST)
# ----------------------------------------------------------------------

@router.post("/admin/incidents/close/{incident_id}")
def incidents_close_submit(
    incident_id: int,
    request: Request,
    user: dict = Depends(load_user_dep),
    gravedad_final: str = Form(...),
):
    _require_admin(user)

    if gravedad_final not in GRAVEDADES:
        return RedirectResponse(
            "/admin/incidents/close?error=gravedad",
            status_code=303,
        )

    close_incident(
        incident_id=incident_id,
        gravedad_final=gravedad_final,
        reviewer_id=user["id"],
        reviewer_name=user["name"],
    )

    return RedirectResponse("/admin/incidents/close", status_code=303)
