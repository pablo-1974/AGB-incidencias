# ui/home.py
import streamlit as st
from datetime import datetime
from pathlib import Path

from ui.styles import apply_global_styles


def render_header(
    app_name: str,
    institution_name: str,
    user: dict | None = None,
    logo_path: str | None = None,
):
    """
    Header común de la aplicación.
    Logo + nombre del centro a la izquierda.
    Usuario + rol + fecha/hora a la derecha.
    """

    apply_global_styles()

    now = datetime.now()

    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    st.markdown('<div class="header-inner">', unsafe_allow_html=True)

    # IZQUIERDA: logo + títulos
    if logo_path and Path(logo_path).exists():
        st.image(logo_path, width=36)

    st.markdown(
        f"""
        <div>
            <div class="header-title">{app_name}</div>
            <div class="header-subtitle">{institution_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # DERECHA: usuario + rol + fecha
    if user:
        name = user.get("name", "")
        role = user.get("role", "")
        st.markdown(
            f"""
            <div class="header-right">
                <div><strong>{name}</strong> ({role})</div>
                <div style="font-size:0.75rem; color:#6b7280;">
                    {now.strftime("%d/%m/%Y")} · {now.strftime("%H:%M")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_footer(institution_name: str, year: int = 2026):
    """
    Footer común de la aplicación.
    """

    st.markdown(
        f"""
        <div class="app-footer">
            © {year} · {institution_name}
        </div>
        """,
        unsafe_allow_html=True,
    )
