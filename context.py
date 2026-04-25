# context.py
"""
Contexto global para todas las plantillas Jinja.
"""

from datetime import datetime
from config import settings


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

        # Layout
        "hide_chrome": extra.get("hide_chrome", False),
    }

    base.update(extra)
    return base
