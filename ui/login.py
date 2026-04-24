# ui/login.py
import streamlit as st
from pathlib import Path
from ui.styles import apply_global_styles
from db.users import authenticate_user


def render_login(app_name: str, institution_name: str, logo_path: str | None = None):
    apply_global_styles()

    # Ocultar sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Contenedor principal
    st.markdown('<div class="login-page">', unsafe_allow_html=True)
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

    st.divider()

    # 🔑 FORMULARIO (ESTO ES LO QUE FALTABA)
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar", use_container_width=True):
        result = authenticate_user(email, password)

        if not result:
            st.error("Credenciales incorrectas.")
            return

        status, user = result

        # Login correcto
        st.session_state["user"] = user
        st.session_state["view"] = "home"
        st.rerun()

    # Cierre contenedores
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
