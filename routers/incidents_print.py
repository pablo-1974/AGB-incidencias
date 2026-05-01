# routers/incidents_print.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from datetime import datetime

from auth import load_user_dep
from utils.permissions import has_permission
from utils.enums import PERM_EDITAR_INCIDENCIA
from db.incidents import get_incident_by_id
from utils.pdf_incident_ticket import incident_ticket_pdf

router = APIRouter()


@router.get("/incidents/print/{incident_id}")
def print_incident_ticket(
    incident_id: int,
    user: dict = Depends(load_user_dep),
):
    # Seguridad: solo quien puede editar puede imprimir
    if not has_permission(user, PERM_EDITAR_INCIDENCIA):
        raise HTTPException(status_code=403)

    inc = get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(status_code=404)

    pdf_bytes = incident_ticket_pdf(
        alumno=inc["alumno"],
        fecha=inc["fecha"],
        hora=inc["hora"],
        profesor=inc["teacher_name"],
        descripcion=inc["descripcion"],
        gravedad_inicial=inc["gravedad_inicial"],
        gravedad_final=inc.get("gravedad_final"),
        enviado_por=user["name"],
        enviado_dt=datetime.now(),
    )

    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=parte_incidencia_{incident_id}.pdf"
        },
    )
