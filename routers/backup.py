# routers/backup.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from datetime import datetime
import io
import openpyxl

from auth import load_user_dep
from utils.permissions import has_permission
from utils.enums import PERM_BACKUP
from db.connection import get_db
from context import ctx

router = APIRouter()


# --------------------------------------------------
# PÁGINA DE BACKUP (UI)
# --------------------------------------------------
@router.get("/admin/backup", response_class=HTMLResponse)
def backup_page(
    request: Request,
    user: dict = Depends(load_user_dep),
):
    if not has_permission(user, PERM_BACKUP):
        raise HTTPException(status_code=403)

    return request.app.state.templates.TemplateResponse(
        "admin/backup.html",
        ctx(
            request,
            user=user,
            title="Copia de seguridad",
        ),
    )


# --------------------------------------------------
# DESCARGA DEL BACKUP (EXCEL)
# --------------------------------------------------
@router.get("/admin/backup/download")
def backup_download(
    user: dict = Depends(load_user_dep),
):
    if not has_permission(user, PERM_BACKUP):
        raise HTTPException(status_code=403)

    wb = openpyxl.Workbook()

    # Hoja INFO
    ws_info = wb.active
    ws_info.title = "INFO"
    ws_info.append(["Aplicación", "Incidencias"])
    ws_info.append(["Fecha backup", datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws_info.append(["Generado por", user["email"]])
    ws_info.append([])
    ws_info.append(["Contenido", "Copia completa de la base de datos"])

    # Exportar tablas
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            tables = [r["table_name"] for r in cur.fetchall()]

            for table in tables:
                ws = wb.create_sheet(title=table)

                cur.execute(f'SELECT * FROM "{table}" LIMIT 1')
