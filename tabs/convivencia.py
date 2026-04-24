# tabs/convivencia.py
import streamlit as st

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create


def render_convivencia(user: dict):
    st.subheader("🧩 Área de Convivencia")

    tabs = st.tabs(
        ["📄 Incidencias", "➕ Nueva incidencia"]
    )

    with tabs[0]:
        render_incidents_list(user, mode="all")

    with tabs[1]:
        render_incident_create(user)
