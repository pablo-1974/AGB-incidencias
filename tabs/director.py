# tabs/director.py
import streamlit as st

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create
from tabs.rankings import render_rankings
from tabs.student_analysis import render_student_analysis

def render_director(user: dict):
    """
    Vista principal del rol DIRECTOR.
    Uso de funcionalidades genéricas.
    """

    st.subheader("📊 Dirección")

    tabs = st.tabs(
        ["📄 Incidencias del centro", "➕ Nueva incidencia"]
    )

    with tabs[0]:
        render_incidents_list(user, mode="all")

    with tabs[1]:
        render_incident_create(user)


    # ==========================
    # RANKINGS
    # ==========================
    st.subheader("📊 Rankings")
    render_rankings(user["role"])

    st.divider()

    # ==========================
    # ANÁLISIS ALUMNO
    # ==========================
    st.subheader("🧒 Análisis por alumno")
    render_student_analysis(user)
