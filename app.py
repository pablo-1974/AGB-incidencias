# app.py
"""
Punto de entrada principal de la aplicación Incidencias.
Configura FastAPI, sesiones, plantillas, estáticos y registra todos los routers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

from config import settings

# Routers principales
from routers.dashboard import router as dashboard_router
from routers.analysis_student import router as analysis_student_router
from routers.analysis_teacher import router as analysis_teacher_router
from routers.analysis_student_pdf import router as analysis_student_pdf_router
from routers.analysis_teacher_pdf import router as analysis_teacher_pdf_router
from routers.rankings import router as rankings_router
from routers.rankings_pdf import router as rankings_pdf_router

# Auth / login
from routers.login import router as login_router
from routers.register_first import router as register_first_router


# ------------------------------------------------------------
# Crear aplicación
# ------------------------------------------------------------
app = FastAPI(title=settings.APP_NAME)

# ------------------------------------------------------------
# Middleware de sesiones
# ------------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="incidencias_session",
    max_age=60 * 60 * 8,  # 8 horas
    same_site="lax",
)

# ------------------------------------------------------------
# Archivos estáticos
# ------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------------------------------------
# Plantillas Jinja2
# ------------------------------------------------------------
templates = Jinja2Templates(directory="templates")

# Guardamos templates en el estado de la app (patrón Ausencias)
app.state.templates = templates

# ------------------------------------------------------------
# Routers
# ------------------------------------------------------------
app.include_router(login_router)
app.include_router(register_first_router)

app.include_router(dashboard_router)
app.include_router(analysis_student_router)
app.include_router(analysis_teacher_router)
app.include_router(analysis_student_pdf_router)
app.include_router(analysis_teacher_pdf_router)
app.include_router(rankings_router)
app.include_router(rankings_pdf_router)

# ------------------------------------------------------------
# Ruta raíz: redirige al dashboard
# ------------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")


# ------------------------------------------------------------
# Health check (útil para Render / despliegue)
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
