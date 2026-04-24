# ui/forms.py
import streamlit as st


def gravedad_selector(
    label: str = "Gravedad",
    key: str = "gravedad",
    help_text: str | None = None,
):
    """
    Selector de gravedad reutilizable.
    Devuelve uno de: 'leve', 'grave', 'muy grave' o None.
    """

    opciones = ["", "leve", "grave", "muy grave"]

    value = st.selectbox(
        label,
        opciones,
        key=key,
        format_func=lambda x: "— Selecciona —" if x == "" else x,
        help=help_text,
    )

    return value if value else None
