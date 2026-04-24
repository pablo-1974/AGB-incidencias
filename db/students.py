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


# ======================================================
# GESTIÓN DE ALUMNOS (ADMIN)
# ======================================================

def upsert_student_by_name(
    *,
    alumno: str,
    grupo: str,
):
    """
    Inserta un alumno nuevo o actualiza su grupo si ya existe.
    El alumno se identifica SOLO por su nombre.
    """
    alumno = alumno.strip()
    grupo = grupo.strip()

    if not alumno or not grupo:
        raise ValueError("Alumno y grupo son obligatorios.")

    with get_db() as conn:
        with conn.cursor() as cur:
            # ¿Existe el alumno?
            cur.execute(
                """
                SELECT grupo
                FROM students
                WHERE alumno = %s
                LIMIT 1
                """,
                (alumno,),
            )
            row = cur.fetchone()

            if row is None:
                # Nuevo alumno
                cur.execute(
                    """
                    INSERT INTO students (grupo, alumno)
                    VALUES (%s, %s)
                    """,
                    (grupo, alumno),
                )
                return "added"

            else:
                current_group = row[0]
                if current_group != grupo:
                    # Cambio de grupo
                    cur.execute(
                        """
                        UPDATE students
                        SET grupo = %s
                        WHERE alumno = %s
                        """,
                        (grupo, alumno),
                    )
                    return "updated"

        return "unchanged"


def change_student_group(
    *,
    alumno: str,
    new_grupo: str,
):
    """
    Cambia manualmente el grupo de un alumno existente.
    """
    alumno = alumno.strip()
    new_grupo = new_grupo.strip()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE students
                SET grupo = %s
                WHERE alumno = %s
                """,
                (new_grupo, alumno),
            )
            return cur.rowcount > 0
