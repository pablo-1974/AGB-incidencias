# db/incidents.py
from datetime import datetime
from db.connection import get_db


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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'abierto', %s)
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
                    estado = 'cerrado',
                    reviewed_by = %s,
                    reviewed_by_name = %s,
                    closed_at = %s
                WHERE id = %s
                """,
                (
                    gravedad_final,
                    reviewer_id,
                    reviewer_name,
                    datetime.now().isoformat(),
                    incident_id,
                ),
            )


# ======================================================
# AVISO INCIDENCIAS ABIERTAS
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
                WHERE estado != 'cerrado'
                LIMIT 1
                """
            )
            return cur.fetchone() is not None
