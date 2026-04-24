# tabs/jefatura.py
import streamlit as st
from tabs.incidents_list import render_incidents_list


def render_jefatura(user: dict):
    st.subheader("📋 Panel de Jefatura")

    render_incidents_list(user, mode="all")

