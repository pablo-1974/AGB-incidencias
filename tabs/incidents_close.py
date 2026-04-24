# tabs/incidents_close.py
import streamlit as st

from db.connection import get_db
from db.incidents import close_incident
from utils.enums import GRAVEDADES, GRAVEDAD_MUY_GRAVE, GRAVEDAD_GRAVE


def _load_pending_incidents():
    """
    Carga la cola de incidencias pendientes,
    ordenadas por prioridad y antigüedad.
    """
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
                    gravedad_inicial,
                    teacher_name
                FROM incidents
                WHERE estado != 'cerrado'
                ORDER BY
                    CASE gravedad_inicial
                        WHEN %s THEN 1
                        WHEN %s THEN 2
                        ELSE 3
                    END,
                    fecha ASC,
                    id ASC
                """,
                (GRAVEDAD_MUY_GRAVE, GRAVEDAD_GRAVE),
            )
            return cur.fetchall()


def render_incidents_close(user: dict):
    st.subheader("✅ Incidencias pendientes de revisión")

    # =========================
    # CARGA COLA
    # =========================
    rows = _load_pending_incidents()

    if not rows:
        st.success("✅ No hay incidencias pendientes.")
        return

    # =========================
    # SELECTOR DE INCIDENCIA
    # =========================
    options = []
    for r in rows:
        label = (
            f"#{r[0]} · {r[3]} ({r[2]}) · "
            f"{r[1]} · {r[5].upper()} · {r[6]}"
        )
        options.append((r[0], label, r))

    selected = st.selectbox(
        "Selecciona una incidencia para revisar",
        options,
        format_func=lambda x: x[1],
    )

    incident_id, _, incident = selected

    # =========================
    # DETALLE
    # =========================
    st.markdown("### 📝 Detalle de la incidencia")
    st.write(incident[4])

    st.markdown(
        f"**Grupo:** {incident[2]}  \n"
        f"**Alumno:** {incident[3]}  \n"
        f"**Fecha:** {incident[1]}  \n"
        f"**Gravedad inicial:** {incident[5]}  \n"
        f"**Profesor:** {incident[6]}"
    )

    # =========================
    # CIERRE
    # =========================
    st.markdown("---")
    st.markdown("### ⚖️ Gravedad final")

    gravedad_final = st.selectbox(
        "Selecciona gravedad final",
        ["— Selecciona gravedad final —"] + GRAVEDADES,
    )

    if gravedad_final == "— Selecciona gravedad final —":
        return

    if st.button("✅ Cerrar incidencia", use_container_width=True):
        close_incident(
            incident_id=incident_id,
            gravedad_final=gravedad_final,
            reviewer_id=user["id"],
            reviewer_name=user["name"],
        )
        st.success("✅ Incidencia cerrada correctamente.")
        st.rerun()
