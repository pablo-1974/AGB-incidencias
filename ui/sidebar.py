# ui/sidebar.py
import streamlit as st


def render_sidebar(user: dict):
    """
    Sidebar común para usuarios autenticados.
    """

    with st.sidebar:
        st.markdown("---")

        # Usuario y rol
        st.write(f"### 👤 {user.get('name', '')}")
        st.caption(f"Rol: {user.get('role', '')}")

        st.markdown("---")

        # Botones globales
        if st.button("🔐 Cambiar contraseña", use_container_width=True):
            st.session_state["view"] = "change_password"

        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")
