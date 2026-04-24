# db/users.py
from db.connection import get_db
from security.passwords import verify_password

from utils.enums import ROLES_TODOS


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
