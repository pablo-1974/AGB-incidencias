# tabs/convivencia.py
import streamlit as st


def render_convivencia(user: dict):
    """
    Vista principal del rol CONVIVENCIA.
    """

    st.subheader("🧩 Área de Convivencia")

    st.write(
        "Seguimiento y resolución de incidencias.\n\n"
        "Funciones previstas:\n"
        "- Casos abiertos\n"
        "- Historial de incidencias\n"
        "- Medidas aplicadas"
    )
