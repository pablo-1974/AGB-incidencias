# app.py
import streamlit as st

from config import APP_NAME, INSTITUTION_NAME, LOGO_PATH, APP_YEAR

from ui.login import render_login
from ui.home import render_header, render_footer
from ui.sidebar import render_sidebar
from ui.first_admin import render_create_first_admin

from db.init import check_db
from db.users import has_any_user
from db.incidents import has_any_open_incident

from utils.enums import ROLES_ADMINISTRATIVOS


# ==============================
# MAIN
# ==============================
def main():
    # --------------------------
    # Configuración Streamlit
    # --------------------------
    st.set_page_config(
        page_title=APP_NAME,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # --------------------------
    # Comprobación BD
    # --------------------------
    try:
        check_db()
    except Exception as e:
        st.error("❌ No se puede conectar con la base de datos.")
        st.exception(e)
        return

    # --------------------------
    # Estado de sesión
    # --------------------------
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("view", "home")

    # ==============================
    # BOOTSTRAP DEL SISTEMA
    # ==============================
    # Si no existe ningún usuario, permitir crear el primer admin
    if not has_any_user():
        render_create_first_admin()
        return

    # ==============================
    # LOGIN
    # ==============================
    if st.session_state["user"] is None:
        render_login(
            app_name=APP_NAME,
            institution_name=INSTITUTION_NAME,
            logo_path=LOGO_PATH,
        )
        return

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
    # AVISO GLOBAL DE INCIDENCIAS ABIERTAS
    # ==============================
    if user.get("role") in ROLES_ADMINISTRATIVOS:
        try:
            if has_any_open_incident():
                st.warning("⚠️ Existen incidencias abiertas en el sistema.")
        except Exception as e:
            st.error("Error al comprobar el estado de las incidencias.")
            st.exception(e)

    # ==============================
    # ROUTING DE VISTAS
    # ==============================
    view = st.session_state["view"]

    if view == "home":
        from tabs.home import render_home
        render_home(user)

    elif view == "change_password":
        from ui.change_password import render_change_password
        render_change_password()

    else:
        st.warning("Vista no reconocida.")

    # ==============================
    # FOOTER
    # ==============================
    render_footer(
        institution_name=INSTITUTION_NAME,
        year=APP_YEAR,
    )


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
