# tabs/profesor.py
import streamlit as st
from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create


def render_profesor(user: dict):
    st.subheader("✏️ Área del profesorado")

    tabs = st.tabs(["📄 Mis incidencias", "➕ Nueva incidencia"])

    with tabs[0]:
        render_incidents_list(user, mode="own")

    with tabs[1]:
        render_incident_create(user)
