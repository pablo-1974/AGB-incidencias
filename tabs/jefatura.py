# tabs/jefatura.py
import streamlit as st

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create
from tabs.incidents_close import render_incidents_close
from tabs.rankings import render_rankings
from tabs.student_analysis import render_student_analysis
from tabs.excursion_eligibility import render_excursion_eligibility

from db.incidents import (
    count_open_incidents,
    count_open_very_serious_incidents,
    count_incidents_created_this_week,
    count_incidents_closed_this_week,
)


def _render_dashboard_jefatura():
    """
    Dashboard (home) de Jefatura.
    KPIs + aviso + botón de acción.
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
            st.session_state["jefatura_focus"] = "close"


def render_jefatura(user: dict):
    st.subheader("📋 Panel de Jefatura")

    # ==========================
    # DASHBOARD (HOME)
    # ==========================
    _render_dashboard_jefatura()

    st.divider()

    
    # ==========================
    # RANKINGS
    # ==========================
    st.subheader("📊 Rankings")
    render_rankings(user["role"])
    
    st.divider()
    
    # ==========================
    # ANÁLISIS ALUMNO
    # ==========================
    
    render_student_analysis(user)
    st.divider()
    
    # ==========================
    # APTOS EXCURSIÓN
    # ==========================
    st.subheader("🎒 No aptos para excursiones")
    render_excursion_eligibility()

    st.divider()
    
    # ==========================
    # NAVEGACIÓN DIRECTA (BOTÓN)
    # ==========================
    if st.session_state.get("jefatura_focus") == "close":
        # Limpiamos el estado para no quedarnos enganchados
        st.session_state.pop("jefatura_focus", None)
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
