# app.py
"""
Punto de entrada principal de la aplicación Incidencias.
Configura FastAPI, sesiones, plantillas, estáticos y registra todos los routers.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

from db.users import has_any_user, get_user_by_id
from auth import load_user_dep

from config import settings

# Routers principales
from routers.analysis_student import router as analysis_student_router
from routers.analysis_teacher import router as analysis_teacher_router
from routers.analysis_student_pdf import router as analysis_student_pdf_router
from routers.analysis_teacher_pdf import router as analysis_teacher_pdf_router
from routers.rankings import router as rankings_router
from routers.rankings_pdf import router as rankings_pdf_router
from routers.admin_users import router as admin_users_router
from routers.admin_dashboard import router as admin_dashboard_router
from routers.incidents_create import router as incidents_create_router

# Auth / login
from routers.login import router as login_router
from routers.register_first import router as register_first_router
from routers.first_login import router as first_login_router

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
app.include_router(first_login_router)

app.include_router(analysis_student_router)
app.include_router(analysis_teacher_router)
app.include_router(analysis_student_pdf_router)
app.include_router(analysis_teacher_pdf_router)
app.include_router(rankings_router)
app.include_router(rankings_pdf_router)
app.include_router(admin_users_router)
app.include_router(admin_dashboard_router)
app.include_router(incidents_create_router)

# ------------------------------------------------------------
# Ruta raíz: redirige al dashboard
# ------------------------------------------------------------
@app.api_route("/", methods=["GET", "HEAD"])
def root(request: Request):

    # HEAD limpio para Render / health checks
    if request.method == "HEAD":
        return JSONResponse({"ok": True})

    # Base de datos vacía → bootstrap
    if not has_any_user():
        return RedirectResponse("/register-first", status_code=303)

    # No sesión → login
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    # Usuario autenticado → decidir dashboard por rol
    user_id = request.session.get("user_id")
    user = get_user_by_id(user_id)
    
    if user["role"] == "admin":
        return RedirectResponse("/admin/dashboard", status_code=303)
    
    # Otros roles (todavía no implementados)
    return RedirectResponse("/login", status_code=303)


# ------------------------------------------------------------
# Health check (útil para Render / despliegue)
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
