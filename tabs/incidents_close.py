# tabs/incidents_close.py
import streamlit as st

from utils.enums import GRAVEDADES
from db.incidents import get_open_incidents, close_incident


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
        rows = get_open_incidents()
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

    selected_label = st.selectbox("Selecciona una incidencia", list(options.keys()))
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
            ["— Selecciona gravedad final —"] + GRAVEDADES
        )
        submit = st.form_submit_button("Cerrar incidencia")

    if not submit:
        return

    if gravedad_final == "— Selecciona gravedad final —":
        st.error("Debes seleccionar la gravedad final antes de cerrar la incidencia.")
        return

    try:
        close_incident(
            incident_id=incident_id,
            gravedad_final=gravedad_final,
            reviewer_id=user["id"],
            reviewer_name=user["name"],
        )
        st.success("✅ Incidencia cerrada correctamente.")
        st.rerun()
    except Exception as e:
        st.error("❌ Error al cerrar la incidencia.")
        st.exception(e)
