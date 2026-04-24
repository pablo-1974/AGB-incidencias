# db/users.py
from db.connection import get_db
from security.passwords import verify_password

from utils.enums import ROLES_TODOS

from security.passwords import hash_password

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
                    email,
                    name,
                    role,
                    password_hash,
                    active
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
        "email": row[1],
        "name": row[2],
        "role": row[3],
        "password_hash": row[4],
        "active": row[5],
    }

    # Validación básica de rol
    if user["role"] not in ROLES_TODOS:
        return None

    return user


def authenticate_user(email: str, password: str):
    """
    Autentica un usuario.

    Devuelve:
      - ("first_login", user_dict)
      - ("ok", user_dict)
      - None
    """
    user = get_user_by_email(email)

    if not user:
        return None

    # Usuario inactivo
    if not user["active"]:
        return None

    # Primer acceso (sin contraseña)
    if user["password_hash"] is None:
        return "first_login", {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        }

    # Contraseña incorrecta
    if not verify_password(password, user["password_hash"]):
        return None

    return "ok", {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }

def has_any_user() -> bool:
    """
    Devuelve True si existe al menos un usuario en la base de datos.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT 1 FROM users);")
            return cur.fetchone()[0]

def create_user(
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    active: bool = True,
):
    """
    Crea un usuario nuevo.
    """
    if role not in ROLES_TODOS:
        raise ValueError("Rol no válido")

    password_hash = hash_password(password)
    active_int = 1 if active else 0   # ✅ conversión correct

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash, role, active)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email.lower(),
                    password_hash,
                    role,
                    active,
                ),
            )
        conn.commit()
