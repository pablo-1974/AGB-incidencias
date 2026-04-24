# config.py
from pathlib import Path

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
# STREAMLIT
# ==============================
LAYOUT = "wide"
SIDEBAR_STATE = "collapsed"

# ==============================
# ROLES (para uso futuro)
# ==============================
ROLE_ADMIN = "admin"
ROLE_JEFATURA = "jefatura"
ROLE_PROFESOR = "profesor"
ROLE_CONVIVENCIA = "convivencia"
