# routers/rankings.py

from collections import Counter
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from db.incidents import get_incidents
from context import ctx
from auth import load_user_dep

router = APIRouter()


@router.get("/rankings", response_class=HTMLResponse)
def rankings(
    request: Request,
    tipo: str = "alumnos",
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Rankings de incidencias por alumnos, profesores o grupos.
    """

    # ---------------------------------
    # 1. Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        fecha_desde=from_,
        fecha_hasta=to,
    )

    counter = Counter()

    for r in rows_raw:
        (
            _id,
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            profesor,
        ) = r

        if tipo == "alumnos":
            counter[alumno] += 1
        elif tipo == "profesores":
            counter[profesor] += 1
        elif tipo == "grupos":
            counter[grupo] += 1

    rows = [
        {"nombre": k, "total": v}
        for k, v in counter.most_common()
    ]

    # ---------------------------------
    # 2. Renderizado
    # ---------------------------------
    return request.app.state.templates.TemplateResponse(
        "rankings.html",
        ctx(
            request,
            user,
            title="Rankings",
            tipo=tipo,
            fecha_desde=from_,
            fecha_hasta=to,
            rows=rows,
        ),
    )
