# routers/rankings_pdf.py

from collections import Counter
from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path

from db.incidents import get_incidents
from auth import load_user_dep
from utils.pdf_ranking_students import pdf_ranking_students
from utils.pdf_ranking_teachers import pdf_ranking_teachers
from utils.pdf_ranking_groups import pdf_ranking_groups

router = APIRouter()


@router.get("/rankings/pdf")
def rankings_pdf(
    request: Request,
    tipo: str = "alumnos",
    from_: str | None = None,
    to: str | None = None,
    user=Depends(load_user_dep),
):
    """
    PDF: Rankings de incidencias.
    """

    # ---------------------------------
    # 1. Cargar incidencias
    # ---------------------------------
    rows_raw = get_incidents(
        mode="all",
        fecha_desde=from_,
        fecha_hasta=to,
    )

    counter = Counter()

    for r in rows_raw:
        (
            _id,
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            profesor,
        ) = r

        if tipo == "alumnos":
            counter[alumno] += 1
        elif tipo == "profesores":
            counter[profesor] += 1
        elif tipo == "grupos":
            counter[grupo] += 1

    ranking = [
        {"nombre": k, "total": v}
        for k, v in counter.most_common()
    ]

    if not ranking:
        return FileResponse(
            path=None,
            media_type="text/plain",
            status_code=404,
            filename="sin_datos.txt",
        )

    # ---------------------------------
    # 2. Generar PDF
    # ---------------------------------
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:

        if tipo == "alumnos":
            pdf_ranking_students(
                ranking=ranking,
                fecha_desde=from_,
                fecha_hasta=to,
                logo_path=Path("static/logo.png"),
                output_path=tmp.name,
            )
            filename = "ranking_alumnos.pdf"

        elif tipo == "profesores":
            pdf_ranking_teachers(
                ranking=ranking,
                fecha_desde=from_,
                fecha_hasta=to,
                logo_path=Path("static/logo.png"),
                output_path=tmp.name,
            )
            filename = "ranking_profesores.pdf"

        elif tipo == "grupos":
            pdf_ranking_groups(
                ranking=ranking,
                fecha_desde=from_,
                fecha_hasta=to,
                logo_path=Path("static/logo.png"),
                output_path=tmp.name,
            )
            filename = "ranking_grupos.pdf"

        else:
            return FileResponse(
                path=None,
                media_type="text/plain",
                status_code=400,
                filename="tipo_invalido.txt",
            )

        return FileResponse(
            tmp.name,
            filename=filename,
            media_type="application/pdf",
        )
