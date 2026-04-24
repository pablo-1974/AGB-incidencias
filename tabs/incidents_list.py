# tabs/incidents_list.py
import streamlit as st
import pandas as pd

from db.connection import get_db


def render_incidents_list(user: dict, mode: str = "own"):
    """
    Lista incidencias con distintos alcances según modo.

    mode:
      - "own"    -> solo incidencias del usuario (profesor)
      - "all"    -> todas las incidencias (jefatura, admin, convivencia)
    """

    st.subheader("📄 Incidencias")

    params = []
    where_clause = ""

    if mode == "own":
        where_clause = "WHERE teacher_id = %s"
        params.append(user["id"])

    # mode == "all"  -> sin WHERE

    query = f"""
        SELECT
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            gravedad_inicial,
            gravedad_final,
            estado,
            teacher_name
        FROM incidents
        {where_clause}
        ORDER BY id DESC
    """

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

    except Exception as e:
        st.error("❌ Error al cargar incidencias.")
        st.exception(e)
        return

    if not rows:
        st.info("No hay incidencias para mostrar.")
        return

    df = pd.DataFrame(
        rows,
        columns=[
            "Fecha",
            "Hora",
            "Grupo",
            "Alumno",
            "Descripción",
            "Gravedad inicial",
            "Gravedad final",
            "Estado",
            "Profesor",
        ],
    )

    st.dataframe(df, use_container_width=True)
