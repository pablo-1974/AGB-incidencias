# tabs/admin.py
import streamlit as st
from tabs.incidents_list import render_incidents_list


def render_admin(user: dict):
    st.subheader("🛠️ Administración")

    render_incidents_list(user, mode="all")
