# auth.py
"""
Autenticación y control de sesión.
Define la dependencia load_user_dep usada en todas las rutas protegidas.
"""

from fastapi import Request, HTTPException
from db.users import get_user_by_id


def load_user_dep(request: Request):
    """
    Dependencia FastAPI.
    Devuelve el usuario autenticado o lanza excepción.
    """
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")

    user = get_user_by_id(user_id)

    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sesión inválida")

    return user
