# ui/login.py
import streamlit as st
from pathlib import Path

from ui.styles import apply_global_styles


def render_login(
    app_name: str,
    institution_name: str,
    logo_path: str | None = None,
):
    """
    Pantalla de login.
    Estética idéntica a la app de Ausencias, con identidad azul turquesa.
    """

    apply_global_styles()

    # Ocultar sidebar en login
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Fondo login
    st.markdown('<div class="login-page">', unsafe_allow_html=True)

    # Tarjeta
    st.markdown('<div class="card login-card">', unsafe_allow_html=True)

    # Logo
    if logo_path and Path(logo_path).exists():
        st.image(logo_path, width=90)

    # Títulos
    st.markdown(
        f"""
        <h1 class="login-title">{app_name}</h1>
        <h2 class="login-subtitle">{institution_name}</h2>
        """,
        unsafe_allow_html=True,
    )

    # Cerrar tarjeta y fondo
    st.markdown("</div>", unsafe_allow_html=True)  # .login-card
    st.markdown("</div>", unsafe_allow_html=True)  # .login-page
