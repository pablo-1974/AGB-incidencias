# db/users.py
from db.connection import get_db
from security.passwords import verify_password


def get_user_by_email(email: str) -> dict | None:
    """
    Devuelve un usuario por email o None si no existe.
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, name, role, password_hash, active
                FROM users
                WHERE email = %s
                """,
                (email.lower(),),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "name": row[2],
        "role": row[3],
        "password_hash": row[4],  # puede ser NULL
        "active": row[5],         # integer 0/1
    }


def authenticate_user(email: str, password: str) -> tuple[str, dict] | None:
    """
    Autentica un usuario.

    DEVUELVE:
      ("ok", user_dict)            -> login correcto
      ("first_login", user_dict)   -> primer acceso (password_hash IS NULL)
      None                         -> error de autenticación
    """

    user = get_user_by_email(email)

    if not user:
        return None

    if not user["active"]:
        return None

    # ✅ PRIMER ACCESO
    if user["password_hash"] is None:
        return "first_login", {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        }

    # ✅ LOGIN NORMAL
    if not verify_password(password, user["password_hash"]):
        return None

    return "ok", {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }
