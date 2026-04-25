# routers/analysis_student.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from db.incidents import get_incidents
from db.students import get_all_students
from utils.enums import GRAVEDAD_MUY_GRAVE
from context import ctx
from auth import load_user_dep

router = APIRouter()


@router.get("/analysis/student", response_class=HTMLResponse)
def analysis_student(
    request: Request,
    alumno: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Análisis de incidencias por alumno.
    """

    # ---------------------------------
    # 1. Alumnos disponibles
    # ---------------------------------
    alumnos = get_all_students()

    # Pantalla inicial (sin alumno seleccionado)
    if not alumno:
        return request.app.state.templates.TemplateResponse(
            "student_analysis.html",  # ✅ nombre real del template
            ctx(
                request,
                user,
                title="Análisis por alumno",
                alumnos=alumnos,
                alumno_sel=None,
                fecha_desde=from_,
                fecha_hasta=to,
                rows=[],
                kpis=None,
            ),
        )

    # ---------------------------------
    # 2. Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        alumno=alumno,
        fecha_desde=from_,
        fecha_hasta=to,
    )

    # ---------------------------------
    # 3. Preparar filas + KPIs
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
            _alumno,
            descripcion,
            gravedad_ini,
            gravedad_fin,
            estado,
            profesor,
        ) = r

        gravedad = gravedad_fin or gravedad_ini

        if estado != "cerrado":
            abiertas += 1

        if gravedad_ini == GRAVEDAD_MUY_GRAVE:
            muy_graves += 1

        rows.append({
            "fecha": fecha,
            "hora": hora,
            "grupo": grupo,
            "profesor": profesor,
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
    # 4. Renderizado final
    # ---------------------------------
    return request.app.state.templates.TemplateResponse(
        "student_analysis.html",  # ✅ nombre real del template
        ctx(
            request,
            user,
            title="Análisis por alumno",
            alumnos=alumnos,
            alumno_sel=alumno,
            fecha_desde=from_,
            fecha_hasta=to,
            rows=rows,
            kpis=kpis,
        ),
    )
