# db/users.py
from db.connection import get_db
from security.passwords import hash_password, verify_password
from utils.enums import ROLES_TODOS


# ----------------------------------------------------------------------
# CONSULTAS BÁSICAS
# ----------------------------------------------------------------------

def get_user_by_id(user_id: int) -> dict | None:
    """
    Devuelve un usuario por ID o None si no existe.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    password_hash,
                    active,
                    must_change_password,
                    created_at,
                    created_by,
                    last_login_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "password_hash": row[4],
        "active": row[5],
        "must_change_password": row[6],
        "created_at": row[7],
        "created_by": row[8],
        "last_login_at": row[9],
    }


def get_user_by_email(email: str) -> dict | None:
    """
    Devuelve un usuario por email o None si no existe.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    password_hash,
                    active,
                    must_change_password
                FROM users
                WHERE email = %s
                """,
                (email.lower(),),
            )
            row = cur.fetchone()

    if not row:
        return None

    user = {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "password_hash": row[4],
        "active": row[5],
        "must_change_password": row[6],
    }

    # Validación defensiva de rol
    if user["role"] not in ROLES_TODOS:
        return None

    return user


def has_any_user() -> bool:
    """
    Devuelve True si existe al menos un usuario en la BD.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT 1 FROM users);")
            return cur.fetchone()[0]


# ----------------------------------------------------------------------
# CREACIÓN DE USUARIOS
# ----------------------------------------------------------------------

def create_first_admin(*, name: str, email: str, password: str):
    """
    Crea el primer usuario administrador.
    SOLO se usa en /register-first.
    """
    password_hash = hash_password(password)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    name,
                    email,
                    role,
                    password_hash,
                    must_change_password,
                    active
                )
                VALUES (%s, %s, 'admin', %s, false, 1)
                """,
                (
                    name,
                    email.lower(),
                    password_hash,
                ),
            )
        conn.commit()


def create_user_admin(
    *,
    name: str,
    email: str,
    role: str,
    created_by: int,
):
    """
    Crea un usuario desde la gestión de usuarios (admin).
    NO define contraseña → forzar primer login.
    """
    if role not in ROLES_TODOS:
        raise ValueError("Rol no válido")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    name,
                    email,
                    role,
                    password_hash,
                    must_change_password,
                    active,
                    created_by
                )
                VALUES (%s, %s, %s, NULL, true, 1, %s)
                """,
                (
                    name,
                    email.lower(),
                    role,
                    created_by,
                ),
            )
        conn.commit()


# ----------------------------------------------------------------------
# ACTUALIZACIÓN DE USUARIO (ADMIN)
# ----------------------------------------------------------------------

def update_user_admin(
    *,
    user_id: int,
    name: str,
    email: str,
    role: str,
):
    """
    Actualiza nombre, email y rol de un usuario.
    """
    if role not in ROLES_TODOS:
        raise ValueError("Rol no válido")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET
                    name = %s,
                    email = %s,
                    role = %s
                WHERE id = %s
                """,
                (
                    name,
                    email.lower(),
                    role,
                    user_id,
                ),
            )
        conn.commit()


def set_user_active(*, user_id: int, active: bool):
    """
    Activa o desactiva un usuario.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET active = %s
                WHERE id = %s
                """,
                (1 if active else 0, user_id),
            )
        conn.commit()


# ----------------------------------------------------------------------
# CONTRASEÑAS
# ----------------------------------------------------------------------

def set_user_password(*, user_id: int, password_hash: str):
    """
    Define la contraseña del usuario y elimina el forzado
    de primer login / reset.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET
                    password_hash = %s,
                    must_change_password = false,
                    last_login_at = now()
                WHERE id = %s
                """,
                (password_hash, user_id),
            )
        conn.commit()


def reset_user_password(*, user_id: int):
    """
    Resetea la contraseña de un usuario.
    El usuario deberá definirla en el próximo login.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET
                    password_hash = NULL,
                    must_change_password = true
                WHERE id = %s
                """,
                (user_id,),
            )
        conn.commit()


# ----------------------------------------------------------------------
# LISTADOS
# ----------------------------------------------------------------------

def get_all_users() -> list[dict]:
    """
    Devuelve todos los usuarios (para gestión admin).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    active,
                    must_change_password,
                    created_at,
                    last_login_at
                FROM users
                ORDER BY name
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "role": r[3],
            "active": r[4],
            "must_change_password": r[5],
            "created_at": r[6],
            "last_login_at": r[7],
        }
        for r in rows
    ]


def get_all_teachers() -> list[dict]:
    """
    Devuelve profesores activos (para análisis).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name
                FROM users
                WHERE role = 'profesor'
                  AND active = 1
                ORDER BY name
                """
            )
            rows = cur.fetchall()

    return [{"id": r[0], "name": r[1]} for r in rows]
