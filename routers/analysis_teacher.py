# routers/analysis_teacher.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from db.incidents import get_incidents
from db.users import get_all_teachers
from utils.enums import GRAVEDAD_MUY_GRAVE
from context import ctx
from auth import load_user_dep

router = APIRouter()


@router.get("/analysis/teacher", response_class=HTMLResponse)
def analysis_teacher(
    request: Request,
    profesor: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Análisis de incidencias por profesor.
    """

    # ---------------------------------
    # Profesores disponibles
    # ---------------------------------
    profesores = get_all_teachers()

    # Pantalla inicial (sin profesor seleccionado)
    if not profesor:
        return request.app.state.templates.TemplateResponse(
            "teacher_analysis.html",   # ✅ NOMBRE REAL
            ctx(
                request,
                user,
                title="Análisis por profesor",
                profesores=profesores,
                profesor_sel=None,
                fecha_desde=from_,
                fecha_hasta=to,
                rows=[],
                kpis=None,
            ),
        )

    # ---------------------------------
    # Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        profesor=profesor,
        fecha_desde=from_,
        fecha_hasta=to,
    )

    # ---------------------------------
    # Preparar filas + KPIs
    # ---------------------------------
    rows = []
    abiertas = 0
    muy_graves = 0

    for r in rows_raw:
        (
            _id,
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            gravedad_ini,
            gravedad_fin,
            estado,
            _profesor,
        ) = r

        gravedad = gravedad_fin or gravedad_ini

        if estado != "cerrado":
            abiertas += 1

        if gravedad_ini == GRAVEDAD_MUY_GRAVE:
            muy_graves += 1

        rows.append({
            "fecha": fecha,
            "alumno": alumno,
            "grupo": grupo,
            "descripcion": descripcion,
            "grav_ini": gravedad_ini,
            "grav_fin": gravedad_fin,
            "gravedad": gravedad,
            "estado": estado,
        })

    kpis = {
        "total": len(rows),
        "abiertas": abiertas,
        "muy_graves": muy_graves,
    }

    # ---------------------------------
    # Renderizado final
    # ---------------------------------
    return request.app.state.templates.TemplateResponse(
        "teacher_analysis.html",   # ✅ NOMBRE REAL
        ctx(
            request,
            user,
            title="Análisis por profesor",
            profesores=profesores,
            profesor_sel=profesor,
            fecha_desde=from_,
            fecha_hasta=to,
            rows=rows,
            kpis=kpis,
        ),
    )
