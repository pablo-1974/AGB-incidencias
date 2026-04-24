# tabs/rankings.py
import streamlit as st

from db.incidents import (
    get_students_ranking,
    get_groups_ranking,
    get_teachers_ranking,
)


def render_rankings(role: str):
    """
    UI de rankings, mostrando lo permitido según el rol.
    """

    st.subheader("📊 Rankings")

    # -------------------------------
    # RANKING DE ALUMNOS
    # -------------------------------
    if role != "profesor":
        st.markdown("### 🧒 Ranking de alumnos")

        rows = get_students_ranking()

        if not rows:
            st.info("No hay incidencias registradas.")
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

    # -------------------------------
    # RANKING DE GRUPOS
    # -------------------------------
    if role != "profesor":
        st.markdown("### 🏫 Ranking de grupos")

        rows = get_groups_ranking()

        if not rows:
            st.info("No hay incidencias registradas.")
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

    # -------------------------------
    # RANKING DE PROFESORES
    # -------------------------------
    if role not in ("profesor", "convivencia"):
        st.markdown("### 👨‍🏫 Ranking de profesores")

        rows = get_teachers_ranking()

        if not rows:
            st.info("No hay incidencias registradas.")
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
