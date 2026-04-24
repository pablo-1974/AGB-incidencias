# db/incidents.py
from datetime import datetime, date, timedelta
from db.connection import get_db

from utils.enums import (
    ESTADO_ABIERTO,
    ESTADO_CERRADO,
    GRAVEDAD_MUY_GRAVE,
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
            hora,
            grupo,
            alumno,
            descripcion,
            gravedad_inicial,
            gravedad_final,
            estado,
            teacher_name
        FROM incidents
        {where_sql}
        ORDER BY fecha DESC, hora DESC, id DESC
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
                    descripcion,
                    gravedad_inicial,
                    estado,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    user_name,
                    grupo,
                    alumno,
                    fecha,
                    "",  # hora no obligatoria
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
            return cur.fetchone()[0]


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
            return cur.fetchone()[0]


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
            return cur.fetchone()[0]


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
            return cur.fetchone()[0]

# ======================================================
# RANKINGS
# ======================================================

def get_students_ranking():
    """
    Ranking de alumnos.
    Devuelve:
      - posicion
      - alumno
      - grupo
      - num_incidencias
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH alumno_grupo_counts AS (
                    SELECT
                        alumno,
                        grupo,
                        COUNT(*) AS cnt
                    FROM incidents
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
                """
            )
            return cur.fetchall()

def get_groups_ranking():
    """
    Ranking de grupos.
    Devuelve:
      - posicion
      - grupo
      - num_incidencias
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, grupo) AS posicion,
                    grupo,
                    COUNT(*) AS num_incidencias
                FROM incidents
                GROUP BY grupo
                ORDER BY num_incidencias DESC, grupo
                """
            )
            return cur.fetchall()

def get_teachers_ranking():
    """
    Ranking de profesores.
    Devuelve:
      - posicion
      - profesor
      - num_incidencias
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, teacher_name) AS posicion,
                    teacher_name AS profesor,
                    COUNT(*) AS num_incidencias
                FROM incidents
                GROUP BY teacher_name
                ORDER BY num_incidencias DESC, profesor
                """
            )
            return cur.fetchall()

