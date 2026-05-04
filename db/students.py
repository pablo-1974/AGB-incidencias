# db/students.py

from db.connection import get_db
from db.students import update_student
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
    incluyendo ID, ordenada por grupo y alumno.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, grupo, alumno
                FROM students
                """
            )
            rows = cur.fetchall()

    rows.sort(
        key=lambda r: (
            normalize_for_sort(r["grupo"]),
            normalize_for_sort(r["alumno"]),
        )
    )

    return [
        {
            "id": r["id"],
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
    - False → ya existía
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


def update_student(
    *,
    student_id: int,
    grupo: str,
    alumno: str,
) -> bool:
    """
    Actualiza el grupo y/o nombre de un alumno por ID.
    Evita duplicados (grupo, alumno).
    """
    grupo = grupo.strip()
    alumno = alumno.strip()

    if not grupo or not alumno:
        raise ValueError("Grupo y alumno son obligatorios")

    with get_db() as conn:
        with conn.cursor() as cur:
            # Evitar duplicados con otro ID
            cur.execute(
                """
                SELECT 1
                FROM students
                WHERE grupo = %s
                  AND alumno = %s
                  AND id <> %s
                """,
                (grupo, alumno, student_id),
            )
            if cur.fetchone():
                return False

            cur.execute(
                """
                UPDATE students
                SET grupo = %s,
                    alumno = %s
                WHERE id = %s
                """,
                (grupo, alumno, student_id),
            )
            updated = cur.rowcount > 0

        conn.commit()

    return updated

# ======================================================
# EDITAR ALUMNO
# ======================================================

@router.post("/admin/students/update/{student_id}")
def update_student_post(
    student_id: int,
    user: dict = Depends(load_user_dep),
    grupo: str = Form(...),
    alumno: str = Form(...),
):
    _require_perm(user)

    updated = update_student(
        student_id=student_id,
        grupo=grupo,
        alumno=alumno,
    )

    if not updated:
        return RedirectResponse(
            "/admin/students?status=exists",
            status_code=303,
        )

    return RedirectResponse(
        "/admin/students?status=updated",
        status_code=303,
    )
