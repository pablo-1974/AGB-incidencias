# db/incidents.py
from datetime import datetime, date, timedelta
from db.connection import get_db
from dateutil.relativedelta import relativedelta

from utils.enums import (
    ESTADO_ABIERTO,
    ESTADO_CERRADO,
    GRAVEDAD_MUY_GRAVE,
    GRAVEDAD_GRAVE,
)

# ======================================================
# CONSULTAS
# ======================================================

def get_incidents(
    *,
    mode: str,
    user_id: int | None = None,
    profesor_id: int | None = None,
    grupo: str | None = None,
    alumno: str | None = None,
    estado: str | None = None,
    gravedad: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    """
    Devuelve incidencias según filtros.

    mode:
      - "own": solo del usuario (requiere user_id)
      - "all": todas
    """

    where = []
    params = []

    if mode == "own":
        where.append("teacher_id = %s")
        params.append(user_id)

    if mode == "all" and profesor_id is not None:
        where.append("teacher_id = %s")
        params.append(profesor_id)

    if grupo:
        where.append("grupo = %s")
        params.append(grupo)

    if alumno:
        where.append("alumno = %s")
        params.append(alumno)

    if estado:
        where.append("estado = %s")
        params.append(estado)

    if gravedad:
        where.append("gravedad_inicial = %s")
        params.append(gravedad)

    if fecha_desde:
        where.append("fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        where.append("fecha <= %s")
        params.append(fecha_hasta)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    query = f"""
        SELECT
            id,
            fecha,
            hora AS franja,
            grupo,
            alumno,
            descripcion,
            gravedad_inicial,
            gravedad_final,
            estado,
            teacher_name
        FROM incidents
        {where_sql}
        ORDER BY fecha DESC, hora_orden DESC, id DESC
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# ======================================================
# CREACIÓN
# ======================================================

def create_incident(
    *,
    user_id: int,
    user_name: str,
    grupo: str,
    alumno: str,
    fecha: str,
    hora: str,
    hora_orden: int,
    descripcion: str,
    gravedad: str,
):
    """
    Inserta una nueva incidencia.
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO incidents (
                    teacher_id,
                    teacher_name,
                    grupo,
                    alumno,
                    fecha,
                    hora,
                    hora_orden,
                    descripcion,
                    gravedad_inicial,
                    estado,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    user_name,
                    grupo,
                    alumno,
                    fecha,
                    hora,
                    hora_orden,
                    descripcion,
                    gravedad,
                    ESTADO_ABIERTO,
                    datetime.now().isoformat(),
                ),
            )


# ======================================================
# CIERRE
# ======================================================

def close_incident(
    *,
    incident_id: int,
    gravedad_final: str,
    reviewer_id: int,
    reviewer_name: str,
):
    """
    Cierra una incidencia y asigna gravedad final.
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE incidents
                SET
                    gravedad_final = %s,
                    estado = %s,
                    reviewed_by = %s,
                    reviewed_by_name = %s,
                    closed_at = %s
                WHERE id = %s
                """,
                (
                    gravedad_final,
                    ESTADO_CERRADO,
                    reviewer_id,
                    reviewer_name,
                    datetime.now().isoformat(),
                    incident_id,
                ),
            )


# ======================================================
# AVISO GLOBAL
# ======================================================

def has_any_open_incident() -> bool:
    """
    Indica si existe al menos una incidencia abierta en el sistema.
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM incidents
                WHERE estado != %s
                LIMIT 1
                """,
                (ESTADO_CERRADO,),
            )
            return cur.fetchone() is not None


# ======================================================
# KPIs — DASHBOARD JEFATURA
# ======================================================

def _start_of_current_week_iso() -> str:
    """
    Devuelve la fecha ISO del lunes de la semana actual.
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def count_open_incidents() -> int:
    """
    Número total de incidencias abiertas (pendientes).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE estado != %s
                """,
                (ESTADO_CERRADO,),
            )
            row = cur.fetchone()
            return next(iter(row.values()))


def count_open_very_serious_incidents() -> int:
    """
    Número de incidencias abiertas con gravedad inicial 'muy grave'.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE estado != %s
                  AND gravedad_inicial = %s
                """,
                (ESTADO_CERRADO, GRAVEDAD_MUY_GRAVE),
            )
            row = cur.fetchone()
            return next(iter(row.values()))


def count_incidents_created_this_week() -> int:
    """
    Número de incidencias creadas desde el lunes de la semana actual.
    """
    since = _start_of_current_week_iso()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE fecha >= %s
                """,
                (since,),
            )
            row = cur.fetchone()
            return next(iter(row.values()))


def count_incidents_closed_this_week() -> int:
    """
    Número de incidencias cerradas desde el lunes de la semana actual.
    """
    since = _start_of_current_week_iso()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE estado = %s
                  AND closed_at >= %s
                """,
                (ESTADO_CERRADO, since),
            )
            row = cur.fetchone()
            return next(iter(row.values()))

# ======================================================
# RANKINGS
# ======================================================

def get_students_ranking(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    """
    Ranking de alumnos.
    Devuelve:
      - posicion
      - alumno
      - grupo
      - num_incidencias
    Permite filtrar por fecha (opcional).
    """
    where = []
    params = []

    if fecha_desde:
        where.append("fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        where.append("fecha <= %s")
        params.append(fecha_hasta)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                WITH alumno_grupo_counts AS (
                    SELECT
                        alumno,
                        grupo,
                        COUNT(*) AS cnt
                    FROM incidents
                    {where_sql}
                    GROUP BY alumno, grupo
                ),
                alumno_totals AS (
                    SELECT
                        alumno,
                        SUM(cnt) AS total_cnt
                    FROM alumno_grupo_counts
                    GROUP BY alumno
                ),
                alumno_main_group AS (
                    SELECT DISTINCT ON (alumno)
                        alumno,
                        grupo
                    FROM alumno_grupo_counts
                    ORDER BY alumno, cnt DESC, grupo
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY at.total_cnt DESC, at.alumno) AS posicion,
                    at.alumno,
                    amg.grupo,
                    at.total_cnt AS num_incidencias
                FROM alumno_totals at
                JOIN alumno_main_group amg
                  ON amg.alumno = at.alumno
                ORDER BY at.total_cnt DESC, at.alumno
                """,
                params,
            )
            return cur.fetchall()

def get_groups_ranking(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    """
    Ranking de grupos.
    Devuelve:
      - posicion
      - grupo
      - num_incidencias
    Permite filtrar por fecha (opcional).
    """
    where = []
    params = []

    if fecha_desde:
        where.append("fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        where.append("fecha <= %s")
        params.append(fecha_hasta)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, grupo) AS posicion,
                    grupo,
                    COUNT(*) AS num_incidencias
                FROM incidents
                {where_sql}
                GROUP BY grupo
                ORDER BY num_incidencias DESC, grupo
                """,
                params,
            )
            return cur.fetchall()

def get_teachers_ranking(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    """
    Ranking de profesores.
    Devuelve:
      - posicion
      - profesor
      - num_incidencias
    Permite filtrar por fecha (opcional).
    """
    where = []
    params = []

    if fecha_desde:
        where.append("fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        where.append("fecha <= %s")
        params.append(fecha_hasta)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, teacher_name) AS posicion,
                    teacher_name AS profesor,
                    COUNT(*) AS num_incidencias
                FROM incidents
                {where_sql}
                GROUP BY teacher_name
                ORDER BY num_incidencias DESC, profesor
                """,
                params,
            )
            return cur.fetchall()

# ======================================================
# ELEGIBLES EXCURSIÓN
# ======================================================
def get_excursion_eligibility(
    *,
    fecha_excursion: str,
    grupos: list[str],
):
    """
    Devuelve dos listas:
      - sancionados
      - posibles_amnistiados

    Cada elemento contiene:
      grupo, alumno, total_faltas, faltas_graves
    """

    fecha_exc = datetime.fromisoformat(fecha_excursion).date()
    fecha_desde = fecha_exc - relativedelta(months=1)
    fecha_hasta = fecha_exc - relativedelta(days=1)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    alumno,
                    grupo,
                    COUNT(*) AS total_faltas,
                    SUM(
                        CASE
                            WHEN gravedad_final IN ('grave', 'muy grave')
                            THEN 1 ELSE 0
                        END
                    ) AS faltas_graves
                FROM incidents
                WHERE estado = %s
                  AND fecha BETWEEN %s AND %s
                  AND grupo = ANY(%s)
                  AND alumno IS NOT NULL
                GROUP BY alumno, grupo
                ORDER BY grupo, alumno
                """,
                (
                    ESTADO_CERRADO,
                    fecha_desde.isoformat(),
                    fecha_hasta.isoformat(),
                    grupos,
                ),
            )

            rows = cur.fetchall()

    sancionados = []
    posibles_amnistiados = []

    for r in rows:
        alumno = r["alumno"]
        grupo = r["grupo"]
        total = r["total_faltas"]
        graves = r["faltas_graves"]
    
        if graves >= 1 or total >= 2:
            sancionados.append({
                "grupo": grupo,
                "alumno": alumno,
                "total": total,
                "graves": graves or 0,
            })
        elif total == 1 and graves == 0:
            posibles_amnistiados.append({
                "grupo": grupo,
                "alumno": alumno,
                "total": total,
                "graves": 0,
            })

    return sancionados, posibles_amnistiados

# ======================================================
# COLA DE CIERRE
# ======================================================

def get_open_incidents_for_closing():
    """
    Devuelve incidencias abiertas ordenadas por:
    1) gravedad (muy grave > grave > resto)
    2) fecha
    3) orden horario
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    fecha,
                    hora AS franja,
                    alumno,
                    descripcion,
                    gravedad_inicial,
                    teacher_name
                FROM incidents
                WHERE estado = %s
                ORDER BY
                    CASE gravedad_inicial
                        WHEN %s THEN 1
                        WHEN %s THEN 2
                        ELSE 3
                    END,
                    fecha ASC,
                    hora_orden ASC,
                    id ASC
                """,
                (
                    ESTADO_ABIERTO,
                    GRAVEDAD_MUY_GRAVE,
                    GRAVEDAD_GRAVE,
                ),
            )
            return cur.fetchall()
