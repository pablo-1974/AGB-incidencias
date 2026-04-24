# tabs/incidents_create.py
import streamlit as st
from datetime import datetime

from db.connection import get_db


def render_incident_create(user: dict):
    """
    Formulario para crear una nueva incidencia.
    Reutilizable para todos los roles.
    """

    st.subheader("➕ Nueva incidencia")

    with st.form("incident_create_form"):
        grupo = st.text_input("Grupo")
        alumno = st.text_input("Alumno")

        fecha = st.date_input("Fecha", value=datetime.today())
        hora = st.time_input("Hora")

        descripcion = st.text_area("Descripción de la incidencia")

        gravedad = st.selectbox(
            "Gravedad inicial",
            ["leve", "grave", "muy grave"]
        )

        submitted = st.form_submit_button("Crear incidencia")

    if not submitted:
        return

    # --------------------------
    # VALIDACIONES BÁSICAS
    # --------------------------
    if not grupo or not alumno or not descripcion:
        st.error("Todos los campos son obligatorios.")
        return

    # --------------------------
    # INSERT EN BD
    # --------------------------
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user["id"],
                        user["name"],
                        grupo,
                        alumno,
                        fecha.isoformat(),
                        hora.strftime("%H:%M"),
                        descripcion,
                        gravedad,
                        "abierto",
                        datetime.now().isoformat(),
                    ),
                )

        st.success("✅ Incidencia creada correctamente")

    except Exception as e:
        st.error("❌ Error al crear la incidencia")
        st.exception(e)
