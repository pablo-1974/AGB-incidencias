# routers/analysis_teacher.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from datetime import date

from auth import load_user_dep
from context import ctx

from db.incidents import get_incidents
from db.users import get_all_teachers
from db.students import get_all_groups, get_students_by_group

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/analysis/teacher", response_class=HTMLResponse)
def analysis_teacher(
    request: Request,
    profesor: str | None = None,
    grupo: str | None = None,
    alumno: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    Historial de incidencias por profesor / grupo / alumno.
    """

    # --------------------------------------------------
    # 1. Fechas por defecto
    # --------------------------------------------------
    fecha_desde = from_ or INICIO_CURSO
    fecha_hasta = to or date.today().isoformat()

    # --------------------------------------------------
    # 2. Filtros disponibles
    # --------------------------------------------------
    profesores = get_all_teachers()
    grupos = get_all_groups()
    alumnos = get_students_by_group(grupo) if grupo else []

    # --------------------------------------------------
    # 3. Incidencias filtradas
    # --------------------------------------------------
    rows_raw = get_incidents(
        mode="all",
        teacher_name=profesor,
        grupo=grupo,
        alumno=alumno,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    # --------------------------------------------------
    # 4. Incidencias totales del sistema (mismo periodo)
    # --------------------------------------------------
    total_rows_raw = get_incidents(
        mode="all",
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    total_sistema = len(total_rows_raw)
    total_filtrado = len(rows_raw)

    if profesor:
        kpi_filtrado_label = f"Incidencias de {profesor}"
    else:
        kpi_filtrado_label = "Incidencias filtradas"

    # --------------------------------------------------
    # 5. Preparar filas
    # (NO incluimos profesor: es el contexto)
    # --------------------------------------------------
    rows = []

    for r in rows_raw:
        rows.append({
            "fecha": r["fecha"],
            "hora": r["franja"],
            "grupo": r["grupo"],
            "alumno": r["alumno"],
            "descripcion": r["descripcion"],
            "grav_ini": r["gravedad_inicial"],
            "grav_fin": r["gravedad_final"],
            "estado": r["estado"],
        })

    # --------------------------------------------------
    # 6. Render
    # --------------------------------------------------
    return request.app.state.templates.TemplateResponse(
        "teacher_analysis.html",
        ctx(
            request,
            user,
            title="Historial por profesor",
            profesores=profesores,
            profesor_sel=profesor,
            grupos=grupos,
            grupo_sel=grupo,
            alumnos=alumnos,
            alumno_sel=alumno,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            rows=rows,
            kpi_total_sistema=total_sistema,
            kpi_filtrado=total_filtrado,
            kpi_filtrado_label=kpi_filtrado_label,
        ),
    )
