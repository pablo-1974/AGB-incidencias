# tabs/admin.py
import streamlit as st


def render_admin(user: dict):
    """
    Vista principal del rol ADMIN.
    Funciones técnicas y de administración del sistema.
    """

    st.subheader("🛠️ Administración del sistema")

    st.write(
        "Área de administración técnica.\n\n"
        "Funciones previstas:\n"
        "- Gestión de usuarios\n"
        "- Reseteo de contraseñas\n"
        "- Auditoría del sistema"
    )
