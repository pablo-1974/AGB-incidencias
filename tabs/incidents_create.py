# tabs/incidents_create.py
import streamlit as st
from datetime import date

from db.students import get_all_groups, get_students_by_group
from db.incidents import create_incident


def render_incident_create(user: dict):
    """
    Formulario para crear una nueva incidencia.
    Grupo -> Alumno dependiente.
    Todos los campos son obligatorios.
    """

    st.subheader("➕ Nueva incidencia")
    st.write("Completa el formulario para enviar la incidencia a Jefatura.")

    # =========================
    # CARGA DE GRUPOS
    # =========================
    try:
        grupos = get_all_groups()
    except Exception as e:
        st.error("❌ Error al cargar los grupos.")
        st.exception(e)
        return

    # =========================
    # FORMULARIO
    # =========================
    with st.form("incident_create_form", clear_on_submit=True):

        grupo = st.selectbox(
            "Grupo",
            ["— Selecciona grupo —"] + grupos
        )

        # ALUMNO DEPENDIENTE DEL GRUPO
        if grupo != "— Selecciona grupo —":
            try:
                alumnos = get_students_by_group(grupo)
            except Exception as e:
                st.error("❌ Error al cargar alumnos.")
                st.exception(e)
                return
            alumno_options = ["— Selecciona alumno —"] + alumnos
        else:
            alumno_options = ["— Selecciona grupo primero —"]

        alumno = st.selectbox(
            "Alumno",
            alumno_options
        )

        fecha = st.date_input(
            "Fecha de la incidencia",
            value=date.today()
        )

        gravedad = st.selectbox(
            "Gravedad de la incidencia",
            [
                "— Selecciona gravedad —",
                "leve",
                "grave",
                "muy grave",
            ],
        )

        descripcion = st.text_area(
            "Descripción de la incidencia",
            height=120
        )

        submitted = st.form_submit_button("📨 Enviar a Jefatura")

    if not submitted:
        return

    # =========================
    # VALIDACIONES
    # =========================
    if grupo == "— Selecciona grupo —":
        st.error("Debes seleccionar un grupo.")
        return

    if alumno in ("— Selecciona grupo primero —", "— Selecciona alumno —"):
        st.error("Debes seleccionar un alumno.")
        return

    if gravedad == "— Selecciona gravedad —":
        st.error("Debes seleccionar la gravedad.")
        return

    if not descripcion.strip():
        st.error("La descripción es obligatoria.")
        return

    # =========================
    # CREACIÓN (DB)
    # =========================
    try:
        create_incident(
            user_id=user["id"],
            user_name=user["name"],
            grupo=grupo,
            alumno=alumno,
            fecha=fecha.isoformat(),
            descripcion=descripcion.strip(),
            gravedad=gravedad,
        )

        st.success("✅ Incidencia enviada correctamente a Jefatura.")

    except Exception as e:
        st.error("❌ Error al enviar la incidencia.")
        st.exception(e)
