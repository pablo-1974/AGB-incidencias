# routers/analysis_student.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from datetime import date

from auth import load_user_dep
from context import ctx

from db.incidents import get_incidents
from db.students import get_all_groups, get_students_by_group

from utils.enums import GRAVEDAD_MUY_GRAVE

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/analysis/student", response_class=HTMLResponse)
def analysis_student(
    request: Request,
    grupo: str | None = None,
    alumno: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Historial de incidencias por alumno.
    Filtros automáticos: grupo, alumno, fechas.
    """

    # --------------------------------------------------
    # 1. Fechas por defecto
    # --------------------------------------------------
    fecha_desde = from_ or INICIO_CURSO
    fecha_hasta = to or date.today().isoformat()

    # --------------------------------------------------
    # 2. Filtros disponibles
    # --------------------------------------------------
    grupos = get_all_groups()
    alumnos = get_students_by_group(grupo) if grupo else []

    # --------------------------------------------------
    # 3. Cargar incidencias filtradas
    # --------------------------------------------------
    rows_raw = get_incidents(
        mode="all",
        grupo=grupo,
        alumno=alumno,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    # --------------------------------------------------
    # 4. Preparar filas y KPIs
    # --------------------------------------------------
    rows = []
    abiertas = 0
    muy_graves = 0

    for r in rows_raw:
        fecha = r["fecha"]
        hora = r["franja"]
        grupo_row = r["grupo"]
        descripcion = r["descripcion"]
        gravedad_ini = r["gravedad_inicial"]
        gravedad_fin = r["gravedad_final"]
        estado = r["estado"]
        profesor = r["teacher_name"]

        gravedad = gravedad_fin or gravedad_ini

        if estado != "cerrado":
            abiertas += 1

        if gravedad_ini == GRAVEDAD_MUY_GRAVE:
            muy_graves += 1

        rows.append({
            "fecha": fecha,
            "hora": hora,
            "grupo": grupo_row,
            "alumno": r["alumno"],
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

    # --------------------------------------------------
    # 5. Render
    # --------------------------------------------------
    return request.app.state.templates.TemplateResponse(
        "student_analysis.html",
        ctx(
            request,
            user,
            title="Historial por alumno",
            grupos=grupos,
            alumnos=alumnos,
            grupo_sel=grupo,
            alumno_sel=alumno,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            rows=rows,
            kpis=kpis,
        ),
    )
