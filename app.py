# app.py
import streamlit as st

from config import APP_NAME, INSTITUTION_NAME, LOGO_PATH, APP_YEAR

from ui.login import render_login
from ui.home import render_header, render_footer
from ui.sidebar import render_sidebar

from db.init import check_db
from db.users import authenticate_user


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
    # Comprobación BD (Neon)
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
    # LOGIN
    # ==============================
    if st.session_state["user"] is None:
        ok, email, password = render_login(
            app_name=APP_NAME,
            institution_name=INSTITUTION_NAME,
            logo_path=LOGO_PATH,
        )

        if ok:
            result = authenticate_user(email, password)

            if result is None:
                st.error("Credenciales incorrectas.")
                return

            status, user = result

            # ✅ PRIMER ACCESO: sin contraseña todavía
            if status == "first_login":
                st.session_state["user"] = user
                st.session_state["view"] = "change_password"
                st.rerun()

            # ✅ LOGIN NORMAL
            if status == "ok":
                st.session_state["user"] = user
                st.session_state["view"] = "home"
                st.rerun()

        # ⚠️ MUY IMPORTANTE:
        # cortar aquí para no renderizar nada más
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
