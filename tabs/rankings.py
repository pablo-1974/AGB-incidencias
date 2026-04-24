# tabs/rankings.py

import streamlit as st
from datetime import date

from db.incidents import (
    get_students_ranking,
    get_groups_ranking,
    get_teachers_ranking,
)

from pathlib import Path

from utils.pdf_ranking_students import pdf_ranking_students
from utils.pdf_ranking_teachers import pdf_ranking_teachers
from utils.pdf_ranking_groups import pdf_ranking_groups

def render_rankings(role: str):
    """
    UI de rankings con filtro opcional por fechas.
    """

    # ==========================
    # FILTRO POR FECHAS
    # ==========================
    with st.expander("📅 Filtro por fechas", expanded=False):
        c1, c2 = st.columns(2)

        fecha_desde = c1.date_input(
            "Desde",
            value=None,
            format="YYYY-MM-DD",
            key=f"rankings_fecha_desde_{role}",
        )

        fecha_hasta = c2.date_input(
            "Hasta",
            value=None,
            format="YYYY-MM-DD",
            key=f"rankings_fecha_hasta_{role}",
        )

    fecha_desde_str = fecha_desde.isoformat() if fecha_desde else None
    fecha_hasta_str = fecha_hasta.isoformat() if fecha_hasta else None

    # ==================================================
    # RANKING DE ALUMNOS
    # ==================================================
    if role != "profesor":
        st.markdown("### 🧒 Ranking de alumnos")

        rows = get_students_ranking(
            fecha_desde=fecha_desde_str,
            fecha_hasta=fecha_hasta_str,
        )

        if not rows:
            st.info("No hay incidencias en el rango seleccionado.")
        else:
            st.dataframe(
                [
                    {
                        "Posición": r[0],
                        "Alumno": r[1],
                        "Grupo": r[2],
                        "Nº incidencias": r[3],
                    }
                    for r in rows
                ],
                use_container_width=True,
                hide_index=True,
            )
            
            # Preparar datos para PDF
            pdf_rows = [
                {
                    "rank": r[0],
                    "alumno": r[1],
                    "grupo": r[2],
                    "partes": r[3],
                }
                for r in rows
            ]

            pdf_bytes = pdf_ranking_students(
                rows=pdf_rows,
                titulo="Ranking de alumnos con más incidencias",
                logo_path=Path("logo.png"),
            )

            st.download_button(
                "📄 Descargar PDF (Ranking de alumnos)",
                data=pdf_bytes,
                file_name="ranking_alumnos.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            
    # ==================================================
    # RANKING DE GRUPOS
    # ==================================================
    if role != "profesor":
        st.markdown("### 🏫 Ranking de grupos")

        rows = get_groups_ranking(
            fecha_desde=fecha_desde_str,
            fecha_hasta=fecha_hasta_str,
        )

        if not rows:
            st.info("No hay incidencias en el rango seleccionado.")
        else:
            st.dataframe(
                [
                    {
                        "Posición": r[0],
                        "Grupo": r[1],
                        "Nº incidencias": r[2],
                    }
                    for r in rows
                ],
                use_container_width=True,
                hide_index=True,
            )
            
            pdf_rows = [
                {
                    "rank": r[0],
                    "grupo": r[1],
                    "partes": r[2],
                }
                for r in rows
            ]

            pdf_bytes = pdf_ranking_groups(
                rows=pdf_rows,
                titulo="Ranking de grupos con más incidencias",
                logo_path=Path("logo.png"),
            )

            st.download_button(
                "📄 Descargar PDF (Ranking de grupos)",
                data=pdf_bytes,
                file_name="ranking_grupos.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    # ==================================================
    # RANKING DE PROFESORES
    # ==================================================
    if role not in ("profesor", "convivencia"):
        st.markdown("### 👨‍🏫 Ranking de profesores")

        rows = get_teachers_ranking(
            fecha_desde=fecha_desde_str,
            fecha_hasta=fecha_hasta_str,
        )

        if not rows:
            st.info("No hay incidencias en el rango seleccionado.")
        else:
            st.dataframe(
                [
                    {
                        "Posición": r[0],
                        "Profesor": r[1],
                        "Nº incidencias": r[2],
                    }
                    for r in rows
                ],
                use_container_width=True,
                hide_index=True,
            )

            pdf_rows = [
                {
                    "rank": r[0],
                    "profesor": r[1],
                    "partes": r[2],
                }
                for r in rows
            ]
            
            pdf_bytes = pdf_ranking_teachers(
                rows=pdf_rows,
                titulo="Ranking de profesores por incidencias",
                logo_path=Path("logo.png"),
            )
            
            st.download_button(
                "📄 Descargar PDF (Ranking de profesores)",
                data=pdf_bytes,
                file_name="ranking_profesores.pdf",
                mime="application/pdf",
                use_container_width=True,
             )
