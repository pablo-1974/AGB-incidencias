# db/students.py
from db.connection import get_db
from utils.text import normalize_for_sort


def get_all_groups() -> list[str]:
    """
    Devuelve la lista de grupos distintos,
    ordenados alfabéticamente según criterio español (a = á).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT grupo
                FROM students
                WHERE grupo IS NOT NULL
                """
            )
            grupos = [r[0] for r in cur.fetchall()]

    grupos.sort(key=normalize_for_sort)
    return grupos


def get_all_students() -> list[str]:
    """
    Devuelve la lista completa de alumnos,
    ordenada alfabéticamente según criterio español.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alumno
                FROM students
                WHERE alumno IS NOT NULL
                """
            )
            alumnos = [r[0] for r in cur.fetchall()]

    alumnos.sort(key=normalize_for_sort)
    return alumnos


def get_students_by_group(grupo: str) -> list[str]:
    """
    Devuelve los alumnos pertenecientes a un grupo concreto,
    ordenados alfabéticamente según criterio español.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alumno
                FROM students
                WHERE grupo = %s
                  AND alumno IS NOT NULL
                """,
                (grupo,),
            )
            alumnos = [r[0] for r in cur.fetchall()]

    alumnos.sort(key=normalize_for_sort)
    return alumnos
