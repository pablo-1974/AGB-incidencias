# tabs/profesor.py
import streamlit as st


def render_profesor(user: dict):
    """
    Vista principal del rol PROFESOR.
    Orquesta las funcionalidades disponibles para el profesor.
    """

    st.subheader("✏️ Área del profesorado")

    st.write(
        "Desde aquí podrás gestionar tus incidencias como docente."
    )

    st.markdown("---")

   
    # ✅ Funcionalidad real: ver mis incidencias
    from tabs.incidents_profesor import render_incidents_profesor
    render_incidents_profesor(user)

