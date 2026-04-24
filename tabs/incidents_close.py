# tabs/incidents_close.py
import streamlit as st
from datetime import datetime

from db.connection import get_db


def render_incidents_close(user: dict):
    """
    Cierre y revisión de incidencias.
    Gravedad final obligatoria.
    """

    st.subheader("✅ Cerrar incidencias")

    # --------------------------
    # Cargar incidencias abiertas
    # --------------------------
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        fecha,
                        grupo,
                        alumno,
                        descripcion,
                        gravedad_inicial
                    FROM incidents
                    WHERE estado != 'cerrado'
                    ORDER BY id DESC
                    """
                )
                rows = cur.fetchall()
    except Exception as e:
        st.error("❌ Error al cargar incidencias abiertas.")
        st.exception(e)
        return

    if not rows:
        st.info("No hay incidencias pendientes de cerrar.")
        return

    # --------------------------
    # Selector de incidencia
    # --------------------------
    options = {
        f"#{r[0]} · {r[1]} · {r[3]} ({r[2]})": r
        for r in rows
    }

    selected_label = st.selectbox(
        "Selecciona una incidencia",
        list(options.keys())
    )

    incident = options[selected_label]
    incident_id = incident[0]

    st.markdown("**Descripción:**")
    st.write(incident[4])

    st.markdown(f"**Gravedad inicial:** {incident[5]}")

    # --------------------------
    # Formulario de cierre
    # --------------------------
    with st.form("close_incident_form"):
        gravedad_final = st.selectbox(
            "Gravedad final (obligatoria)",
            [
                "— Selecciona gravedad final —",
                "leve",
                "grave",
                "muy grave",
            ],
        )

        submit = st.form_submit_button("Cerrar incidencia")

    if not submit:
        return

    # --------------------------
    # VALIDACIÓN OBLIGATORIA
    # --------------------------
    if gravedad_final == "— Selecciona gravedad final —":
        st.error("Debes seleccionar la gravedad final antes de cerrar la incidencia.")
        return

    # --------------------------
    # UPDATE EN BD
    # --------------------------
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE incidents
                    SET
                        gravedad_final = %s,
                        estado = 'cerrado',
                        reviewed_by = %s,
                        reviewed_by_name = %s,
                        closed_at = %s
                    WHERE id = %s
                    """,
                    (
                        gravedad_final,
                        user["id"],
                        user["name"],
                        datetime.now().isoformat(),
                        incident_id,
                    ),
                )

        st.success("✅ Incidencia cerrada correctamente.")
        st.rerun()

    except Exception as e:
        st.error("❌ Error al cerrar la incidencia.")
        st.exception(e)
