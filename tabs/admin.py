# tabs/admin.py
import streamlit as st

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create
from tabs.incidents_close import render_incidents_close

from db.incidents import (
    count_open_incidents,
    count_open_very_serious_incidents,
    count_incidents_created_this_week,
    count_incidents_closed_this_week,
)


def _render_dashboard_admin():
    """
    Dashboard (home) de Administración.
    Reutiliza exactamente los KPIs de Jefatura.
    """

    # ==========================
    # KPIs
    # ==========================
    pending = count_open_incidents()
    very_serious = count_open_very_serious_incidents()
    created_week = count_incidents_created_this_week()
    closed_week = count_incidents_closed_this_week()

    # ==========================
    # AVISO / ESTADO GENERAL
    # ==========================
    if pending == 0:
        st.success("✅ No hay incidencias pendientes.")
    elif very_serious > 0:
        st.error("🚨 Hay incidencias muy graves pendientes de revisar.")
    else:
        st.warning("⚠️ Hay incidencias pendientes de revisar.")

    # ==========================
    # KPIs VISUALES
    # ==========================
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("📬 Pendientes", pending)

    with c2:
        st.metric("🚨 Muy graves", very_serious)

    with c3:
        st.metric("📅 Esta semana", created_week)

    with c4:
        st.metric("✅ Cerradas", closed_week)

    # ==========================
    # BOTÓN DE ACCIÓN
    # ==========================
    if pending > 0:
        if st.button("✅ Revisar incidencias pendientes", use_container_width=True):
            st.session_state["admin_focus"] = "close"


def render_admin(user: dict):
    st.subheader("🛠️ Administración")

    # ==========================
    # DASHBOARD (HOME)
    # ==========================
    _render_dashboard_admin()

    st.divider()

    # ==========================
    # NAVEGACIÓN DIRECTA (BOTÓN)
    # ==========================
    if st.session_state.get("admin_focus") == "close":
        st.session_state.pop("admin_focus", None)
        render_incidents_close(user)
        return

    # ==========================
    # TABS NORMALES
    # ==========================
    tabs = st.tabs(
        ["📄 Incidencias", "➕ Nueva incidencia", "✅ Cerrar incidencia"]
    )

    with tabs[0]:
        render_incidents_list(user, mode="all")

    with tabs[1]:
        render_incident_create(user)

    with tabs[2]:
        render_incidents_close(user)
