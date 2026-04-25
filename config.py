# config.py
from pathlib import Path
import os


class Settings:
    # ==============================
    # APLICACIÓN
    # ==============================
    APP_NAME = "Incidencias de alumnado"
    INSTITUTION_NAME = "AGB Antonio García Bellido"
    APP_YEAR = 2026

    # ==============================
    # RUTAS
    # ==============================
    BASE_DIR = Path(__file__).resolve().parent
    LOGO_PATH = str(BASE_DIR / "logo.png")

    # ==============================
    # SEGURIDAD
    # ==============================
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # ==============================
    # BASE DE DATOS
    # ==============================
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # ==============================
    # ROLES
    # ==============================
    ROLE_ADMIN = "admin"
    ROLE_JEFATURA = "jefatura"
    ROLE_DIRECTOR = "director"
    ROLE_CONVIVENCIA = "convivencia"
    ROLE_PROFESOR = "profesor"

# ✅ Instancia única que espera el resto del proyecto
settings = Settings()
