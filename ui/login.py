# ui/login.py
import streamlit as st
from pathlib import Path

from ui.styles import apply_global_styles
from db.users import authenticate_user


def render_login(
    app_name: str,
    institution_name: str,
    logo_path: str | None = None,
):
    # CSS global (ya correcto)
    apply_global_styles()

    # Ocultar sidebar SOLO en login
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Un poco de aire arriba
    st.markdown("##")

    # Centrado horizontal REAL (Streamlit)
    left, center, right = st.columns([1, 2, 1])

    with center:
        # Tarjeta visual
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Logo
        if logo_path and Path(logo_path).exists():
            st.image(logo_path, width=80)

        # Título y subtítulo
        st.markdown(
            f"""
            <div class="login-title">{app_name}</div>
            <div class="login-subtitle">{institution_name}</div>
            """,
            unsafe_allow_html=True,
        )

        # Campos
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        # Botón
        if st.button("Entrar", use_container_width=True):
            result = authenticate_user(email, password)

            if not result:
                st.error("Credenciales incorrectas.")
                return

            status, user = result
            st.session_state["user"] = user
            st.session_state["view"] = "home"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
