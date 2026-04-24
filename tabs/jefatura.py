# tabs/jefatura.py
import streamlit as st


def render_jefatura(user: dict):
    """
    Vista principal de JEFATURA.
    """

    st.subheader("📋 Panel de Jefatura")

    st.write(
        "Gestión académica y organizativa del centro.\n\n"
        "Funciones previstas:\n"
        "- Incidencias\n"
        "- Alumnado\n"
        "- Convivencia\n"
        "- Informes"
    )
