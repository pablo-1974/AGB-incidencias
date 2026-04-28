# utils/permissions.py
"""
Sistema centralizado de permisos funcionales.

Este módulo define:
- cómo comprobar si un usuario puede realizar una acción
- usando los permisos funcionales definidos en utils.enums
"""

from utils.enums import PERMISSIONS_BY_ROLE


def has_permission(user: dict | None, permission: str) -> bool:
    """
    Comprueba si el usuario tiene un permiso funcional concreto.

    :param user: diccionario de usuario (ctx / load_user_dep)
    :param permission: constante PERM_*
    :return: True si está autorizado, False en caso contrario
    """
    if not user:
        return False

    role = user.get("role")
    if not role:
        return False

    return role in PERMISSIONS_BY_ROLE.get(permission, set())
