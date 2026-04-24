# app.py
import streamlit as st

from ui.login import render_login
from ui.home import render_header, render_footer
from ui.sidebar import render_sidebar


# ==============================
# CONFIGURACIÓN GENERAL
# ==============================
from config import APP_NAME, INSTITUTION_NAME, LOGO_PATH, APP_YEAR


# ==============================
# MOCK AUTENTICACIÓN (TEMPORAL)
# ==============================
def authenticate(email: str, password: str):
    """
    Autenticación provisional.
    Sustituir por lógica real (BD).
    """
    if email and password:
        return {
            "name": "Pablo Ceballos Roa",
            "role": "admin",
            "email": email,
        }
    return None


# ==============================
# MAIN
# ==============================
def main():
    st.set_page_config(
        page_title=APP_NAME,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inicializar estado
    if "user" not in st.session_state:
        st.session_state["user"] = None

    if "view" not in st.session_state:
        st.session_state["view"] = "home"

    # ==============================
    # LOGIN
    # ==============================
    if st.session_state["user"] is None:
        ok, email, password = render_login(
            app_name=APP_NAME,
            institution_name=INSTITUTION_NAME,
            logo_path=LOGO_PATH,
        )

        if ok:
            user = authenticate(email, password)
            if user:
                st.session_state["user"] = user
                st.session_state["view"] = "home"
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

        return  # OBLIGATORIO: no seguir renderizando

    # ==============================
    # USUARIO AUTENTICADO
    # ==============================
    user = st.session_state["user"]

    # HEADER
    render_header(
        app_name=APP_NAME,
        institution_name=INSTITUTION_NAME,
        user=user,
        logo_path=LOGO_PATH,
    )

    # SIDEBAR
    render_sidebar(user)

    # ==============================
    # ROUTING DE VISTAS
    # ==============================
    view = st.session_state.get("view", "home")

    if view == "home":
        st.title("🏠 Inicio")
        st.write("Bienvenido a la aplicación de incidencias.")
        st.write("Aquí irán los accesos por rol.")

    elif view == "change_password":
        st.title("🔐 Cambiar contraseña")
        st.info("Aquí irá el formulario de cambio de contraseña.")

    else:
        st.warning("Vista no reconocida")

    # ==============================
    # FOOTER
    # ==============================
    render_footer(
        institution_name=INSTITUTION_NAME,
        year=2026,
    )


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
