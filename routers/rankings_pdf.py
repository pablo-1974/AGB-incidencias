# routers/rankings_pdf.py

from collections import Counter
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response

from auth import load_user_dep
from db.incidents import get_incidents
from utils.pdf_rankings import pdf_rankings

router = APIRouter()

INICIO_CURSO = "2025-09-01"


@router.get("/rankings/pdf")
def rankings_pdf(
    request: Request,
    mode: str = "alumnos",
    gravedad: str | None = None,
    grupo: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    fecha_desde = from_ or INICIO_CURSO
    fecha_hasta = to or date.today().isoformat()

    rows_raw = get_incidents(
        mode="all",
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    counter = Counter()

    # -------- Título y columna --------
    if mode == "alumnos":
        columna = "Alumno"
        if grupo:
            titulo = f"Ranking de alumnos de {grupo}"
        else:
            titulo = "Ranking de alumnos"
    elif mode == "grupos":
        columna = "Grupo"
        titulo = "Ranking de grupos"
    else:
        columna = "Profesor"
        titulo = "Ranking de profesores"

    # -------- Agregación --------
    for r in rows_raw:
        grav_real = r["gravedad_final"] or r["gravedad_inicial"]
        if gravedad and grav_real != gravedad:
            continue

        if mode == "alumnos":
            if grupo and r["grupo"] != grupo:
                continue
            key = r["alumno"]
        elif mode == "grupos":
            key = r["grupo"]
        else:
            key = r["teacher_name"]

        if key:
            counter[key] += 1

    rows = [
        {"nombre": k, "total": v}
        for k, v in counter.most_common()
    ]

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No hay datos para generar el ranking",
        )

    pdf_bytes = pdf_rankings(
        rows=rows,
        titulo=titulo,
        columna=columna,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        logo_path=Path("static/logo.png"),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=ranking_incidencias.pdf"
        },
    )

