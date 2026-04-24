# tabs/jefatura.py
import streamlit as st

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create
from tabs.incidents_close import render_incidents_close


def render_jefatura(user: dict):
    st.subheader("📋 Panel de Jefatura")

    tabs = st.tabs(
        ["📄 Incidencias", "➕ Nueva incidencia", "✅ Cerrar incidencia"]
    )

    with tabs[0]:
        render_incidents_list(user, mode="all")

    with tabs[1]:
        render_incident_create(user)

    with tabs[2]:
        render_incidents_close(user)
