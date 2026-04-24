# db/students.py
from db.connection import get_db


def get_all_groups():
    """
    Devuelve la lista de grupos distintos.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT grupo
                FROM students
                ORDER BY grupo
                """
            )
            return [r[0] for r in cur.fetchall() if r[0]]


def get_all_students():
    """
    Devuelve la lista completa de alumnos.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alumno
                FROM students
                ORDER BY alumno
                """
            )
            return [r[0] for r in cur.fetchall() if r[0]]


def get_students_by_group(grupo: str):
    """
    Devuelve los alumnos pertenecientes a un grupo concreto.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alumno
                FROM students
                WHERE grupo = %s
                ORDER BY alumno
                """,
                (grupo,),
            )
            return [r[0] for r in cur.fetchall() if r[0]]
