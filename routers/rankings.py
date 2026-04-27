# routers/rankings.py

from collections import Counter
from datetime import date
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from db.incidents import get_incidents
from context import ctx
from auth import load_user_dep

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/rankings", response_class=HTMLResponse)
def rankings(
    request: Request,
    mode: str = "alumnos",              # alumnos | grupos | profesores
    gravedad: str | None = None,         # leve | grave | muy_grave | None
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Rankings de incidencias.
    """

    fecha_desde = from_ or INICIO_CURSO
    fecha_hasta = to or date.today().isoformat()

    rows_raw = get_incidents(
        mode="all",
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    counter = Counter()

    for r in rows_raw:
        # Filtro por gravedad
        gravedad_real = r["gravedad_final"] or r["gravedad_inicial"]
        if gravedad and gravedad_real != gravedad:
            continue

        if mode == "alumnos":
            key = r["alumno"]
            titulo = "Ranking de alumnos"
            columna = "Alumno"
        elif mode == "grupos":
            key = r["grupo"]
            titulo = "Ranking de grupos"
            columna = "Grupo"
        else:
            key = r["teacher_name"]
            titulo = "Ranking de profesores"
            columna = "Profesor"

        if key:
            counter[key] += 1

    rows = [
        {"nombre": k, "total": v}
        for k, v in counter.most_common()
    ]

    return request.app.state.templates.TemplateResponse(
        "rankings.html",
        ctx(
            request,
            user,
            title=titulo,
            mode=mode,
            columna=columna,
            gravedad=gravedad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            rows=rows,
        ),
    )
