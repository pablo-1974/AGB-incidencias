# tabs/incidents_profesor.py
import streamlit as st
import pandas as pd

from db.connection import get_db


def render_incidents_profesor(user: dict):
    """
    Muestra las incidencias creadas por el profesor autenticado.
    Solo lectura (por ahora).
    """

    st.markdown("### 📄 Mis incidencias")

    teacher_id = user.get("id")
    if not teacher_id:
        st.error("Usuario no válido.")
        return

    # --------------------------
    # CONSULTA A BD (Neon)
    # --------------------------
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        fecha,
                        hora,
                        grupo,
                        alumno,
                        descripcion,
                        gravedad_inicial,
                        estado
                    FROM incidents
                    WHERE teacher_id = %s
                    ORDER BY id DESC
                    """,
                    (teacher_id,),
                )
                rows = cur.fetchall()

    except Exception as e:
        st.error("❌ Error al cargar las incidencias.")
        st.exception(e)
        return

    if not rows:
        st.info("No has registrado ninguna incidencia todavía.")
        return

    # --------------------------
    # DATAFRAME
    # --------------------------
    df = pd.DataFrame(
        rows,
        columns=[
            "Fecha",
            "Hora",
            "Grupo",
            "Alumno",
            "Descripción",
            "Gravedad",
            "Estado",
        ],
    )

    st.dataframe(df, use_container_width=True)
