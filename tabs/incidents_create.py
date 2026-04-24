# tabs/incidents_create.py
import streamlit as st
from datetime import date

from db.connection import get_db


def render_incident_create(user: dict):
    """
    Formulario para crear una nueva incidencia.
    Todos los campos son obligatorios.
    """

    st.subheader("➕ Nueva incidencia")
    st.write("Completa el formulario para enviar la incidencia a Jefatura.")

    # =========================
    # CARGA DE OPCIONES
    # =========================
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT grupo FROM students ORDER BY grupo")
                grupos = [r[0] for r in cur.fetchall() if r[0]]

                cur.execute("SELECT alumno FROM students ORDER BY alumno")
                alumnos = [r[0] for r in cur.fetchall() if r[0]]

    except Exception as e:
        st.error("❌ Error al cargar grupos o alumnos.")
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

        alumno = st.selectbox(
            "Alumno",
            ["— Selecciona alumno —"] + alumnos
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

    if alumno == "— Selecciona alumno —":
        st.error("Debes seleccionar un alumno.")
        return

    if gravedad == "— Selecciona gravedad —":
        st.error("Debes seleccionar la gravedad.")
        return

    if not descripcion.strip():
        st.error("La descripción es obligatoria.")
        return

    # =========================
    # INSERT EN BD
    # =========================
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO incidents (
                        teacher_id,
                        teacher_name,
                        grupo,
                        alumno,
                        fecha,
                        hora,
                        descripcion,
                        gravedad_inicial,
                        estado,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        user["id"],
                        user["name"],
                        grupo,
                        alumno,
                        fecha.isoformat(),
                        "",  # hora vacía (no obligatoria ahora)
                        descripcion.strip(),
                        gravedad,
                        "abierto",
                    ),
                )

        st.success("✅ Incidencia enviada correctamente a Jefatura.")

    except Exception as e:
        st.error("❌ Error al enviar la incidencia.")
        st.exception(e)
