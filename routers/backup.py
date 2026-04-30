# routers/backup.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from datetime import datetime
import io
import openpyxl

from auth import load_user_dep
from utils.permissions import has_permission
from utils.enums import PERM_BACKUP
from db.connection import get_db

router = APIRouter()


@router.get("/admin/backup")
def download_backup(user: dict = Depends(load_user_dep)):
    if not has_permission(user, PERM_BACKUP):
        raise HTTPException(status_code=403)

    wb = openpyxl.Workbook()

    # --------------------------------------------------
    # Hoja INFO
    # --------------------------------------------------
    ws_info = wb.active
    ws_info.title = "INFO"

    ws_info.append(["Aplicación", "Incidencias"])
    ws_info.append(["Fecha backup", datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws_info.append(["Generado por", user["email"]])
    ws_info.append([])
    ws_info.append(["Contenido", "Copia completa de la base de datos"])

    # --------------------------------------------------
    # Exportar tablas reales
    # --------------------------------------------------
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
                columns = [desc[0] for desc in cur.description]
                ws.append(columns)

                cur.execute(f'SELECT * FROM "{table}"')
                for row in cur.fetchall():
                    ws.append(list(row.values()))

    # --------------------------------------------------
    # Descargar Excel
    # --------------------------------------------------
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"incidencias_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return Response(
        stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )
