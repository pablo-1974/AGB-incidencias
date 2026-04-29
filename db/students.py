# db/students.py

from db.connection import get_db
from utils.text import normalize_for_sort


# ======================================================
# CONSULTAS (LECTURA)
# ======================================================

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
            grupos = [r["grupo"] for r in cur.fetchall()]

    grupos.sort(key=normalize_for_sort)
    return grupos


def get_all_students() -> list[dict]:
    """
    Devuelve la lista completa de alumnos con su grupo,
    ordenada por grupo y alumno según criterio español.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT grupo, alumno
                FROM students
                """
            )
            rows = cur.fetchall()

    rows.sort(key=lambda r: (normalize_for_sort(r["grupo"]),
                              normalize_for_sort(r["alumno"])))

    return [
        {
            "grupo": r["grupo"],
            "alumno": r["alumno"],
        }
        for r in rows
    ]


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
                """,
                (grupo,),
            )
            alumnos = [r["alumno"] for r in cur.fetchall()]

    alumnos.sort(key=normalize_for_sort)
    return alumnos


# ======================================================
# GESTIÓN DE ALUMNOS (ADMIN)
# ======================================================

def student_exists(*, grupo: str, alumno: str) -> bool:
    """
    Comprueba si existe un alumno con esa combinación (grupo, alumno).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM students
                WHERE grupo = %s
                  AND alumno = %s
                """,
                (grupo, alumno),
            )
            return cur.fetchone() is not None


def create_student_if_not_exists(*, grupo: str, alumno: str) -> bool:
    """
    Crea un alumno si no existe la combinación (grupo, alumno).

    Devuelve:
    - True  → alumno creado
    - False → ya existía (no se hace nada)
    """
    grupo = grupo.strip()
    alumno = alumno.strip()

    if not grupo or not alumno:
        raise ValueError("Grupo y alumno son obligatorios")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM students
                WHERE grupo = %s
                  AND alumno = %s
                """,
                (grupo, alumno),
            )

            if cur.fetchone():
                return False

            cur.execute(
                """
                INSERT INTO students (grupo, alumno)
                VALUES (%s, %s)
                """,
                (grupo, alumno),
            )
        conn.commit()

    return True


def change_student_group(
    *,
    grupo_actual: str,
    alumno: str,
    nuevo_grupo: str,
) -> bool:
    """
    Cambia manualmente el grupo de un alumno existente.
    Acción explícita (NO usada en importaciones).
    """
    alumno = alumno.strip()
    grupo_actual = grupo_actual.strip()
    nuevo_grupo = nuevo_grupo.strip()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE students
                SET grupo = %s
                WHERE grupo = %s
                  AND alumno = %s
                """,
                (nuevo_grupo, grupo_actual, alumno),
            )
            updated = cur.rowcount > 0
        conn.commit()

    return updated
