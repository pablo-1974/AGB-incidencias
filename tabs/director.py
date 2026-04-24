# tabs/director.py
import streamlit as st


def render_director(user: dict):
    """
    Vista principal del rol DIRECTOR.
    """

    st.subheader("📊 Dirección")

    st.write(
        "Visión global del estado del centro.\n\n"
        "Funciones previstas:\n"
        "- Informes generales\n"
        "- Estadísticas\n"
        "- Seguimiento institucional"
    )
