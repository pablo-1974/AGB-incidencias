# tabs/home.py
import streamlit as st


def render_home(user: dict):
    """
    Vista principal de la aplicación.
    Muestra contenido diferente según el rol del usuario.
    """

    role = user.get("role")
    st.title("🏠 Inicio")

    if role == "admin":
        render_home_admin()

    elif role == "jefatura":
        render_home_jefatura()

    elif role == "profesor":
        render_home_profesor()

    elif role == "convivencia":
        render_home_convivencia()

    elif role == "director":
        render_home_director()

    else:
        st.warning("Rol no reconocido.")


# ==============================
# VISTAS POR ROL
# ==============================

def render_home_admin():
    st.subheader("🛠️ Administración del sistema")
    st.write(
        "Área técnica de administración de la aplicación.\n\n"
        "Desde aquí se gestionará:\n"
        "- Usuarios y roles\n"
        "- Reseteo de contraseñas\n"
        "- Parámetros generales del sistema\n"
        "- Auditoría y mantenimiento"
    )


def render_home_jefatura():
    st.subheader("📋 Panel de Jefatura")
    st.write(
        "Área de gestión académica y organizativa del centro.\n\n"
        "Funciones previstas:\n"
        "- Gestión de incidencias\n"
        "- Gestión de alumnado\n"
        "- Convivencia\n"
        "- Informes y estadísticas"
    )


def render_home_profesor():
    st.subheader("✏️ Área del profesorado")
    st.write(
        "Gestión de tus incidencias como docente.\n\n"
        "Funciones previstas:\n"
        "- Crear incidencias\n"
        "- Consultar incidencias propias\n"
        "- Seguimiento de estados"
    )


def render_home_convivencia():
    st.subheader("🧩 Área de Convivencia")
    st.write(
        "Seguimiento y resolución de incidencias relacionadas con convivencia.\n\n"
        "Funciones previstas:\n"
        "- Casos en seguimiento\n"
        "- Historial de incidencias\n"
        "- Aplicación de medidas"
    )


def render_home_director():
    st.subheader("📊 Dirección")
    st.write(
        "Visión global del estado del centro.\n\n"
        "Funciones previstas:\n"
        "- Informes generales\n"
        "- Estadísticas globales\n"
        "- Seguimiento institucional"
    )
