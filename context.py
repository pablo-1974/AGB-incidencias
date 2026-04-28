# context.py
"""
Contexto global para todas las plantillas Jinja.
"""

from datetime import datetime
from config import settings

from utils.enums import (
    ROLE_ADMIN,
    ROLE_JEFE,
    ROLE_DIRECTOR,
    ROLE_SECRETARIO,
    ROLE_CONVIVENCIA,
    ROLE_ORIENTADOR,
    ROLE_PROFESOR,
)
from utils.permissions import has_permission

def ctx(request, user=None, **extra):
    """
    Construye el contexto base para las plantillas.
    """
    now = datetime.now()

    base = {
        "request": request,
        "user": user,
        "title": extra.get("title", settings.APP_NAME),

        # App / centro
        "app_name": settings.APP_NAME,
        "institution_name": settings.INSTITUTION_NAME,
        "year": settings.APP_YEAR,
        "now_dt": now,
        "logo_url": "/static/logo.png",
        
        # Layout
        "hide_chrome": extra.get("hide_chrome", False),

        # ✅ ROLES DISPONIBLES EN JINJA
        "ROLE_ADMIN": ROLE_ADMIN,
        "ROLE_JEFE": ROLE_JEFE,
        "ROLE_DIRECTOR": ROLE_DIRECTOR,
        "ROLE_SECRETARIO": ROLE_SECRETARIO,
        "ROLE_CONVIVENCIA": ROLE_CONVIVENCIA,
        "ROLE_ORIENTADOR": ROLE_ORIENTADOR,
        "ROLE_PROFESOR": ROLE_PROFESOR,
        
        # ✅ Permisos funcionales
        "has_permission": has_permission,
    }

    base.update(extra)
    return base
