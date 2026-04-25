# config.py

import os


class Settings:
    # Información de la app
    APP_NAME = "Incidencias"
    INSTITUTION_NAME = "IES Antonio García Bellido"

    # Seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Base de datos
    DATABASE_URL = os.environ.get("DATABASE_URL")


# Instancia única de configuración
settings = Settings()
