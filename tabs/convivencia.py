# tabs/convivencia.py
import streamlit as st
from tabs.incidents_list import render_incidents_list


def render_convivencia(user: dict):
    st.subheader("🧩 Área de Convivencia")

    render_incidents_list(user, mode="all")
