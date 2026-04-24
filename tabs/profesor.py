# tabs/profesor.py
import streamlit as st

from tabs.incidents_list import render_incidents_profesor
from tabs.incidents_create import render_incident_create


def render_profesor(user: dict):
    st.subheader("✏️ Área del profesorado")

    tab_list, tab_create = st.tabs(
        ["📄 Mis incidencias", "➕ Nueva incidencia"]
    )

    with tab_list:
        render_incidents_profesor(user)

    with tab_create:
        render_incident_create(user)
