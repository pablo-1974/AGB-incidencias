# tabs/home.py
import streamlit as st


def render_home(user: dict):
    role = user.get("role")
    st.title("🏠 Inicio")

    if role == "admin":
        from tabs.admin import render_admin
        render_admin(user)

    elif role == "jefatura":
        from tabs.jefatura import render_jefatura
        render_jefatura(user)

    elif role == "profesor":
        from tabs.profesor import render_profesor
        render_profesor(user)

    elif role == "convivencia":
        from tabs.convivencia import render_convivencia
        render_convivencia(user)

    elif role == "director":
        from tabs.director import render_director
        render_director(user)

    else:
        st.warning("Rol no reconocido.")


