# tabs/excursion_eligibility.py
import streamlit as st
from datetime import date
from pathlib import Path

from dateutil.relativedelta import relativedelta

from db.incidents import get_excursion_eligibility
from db.students import get_all_groups
from utils.pdf_excursion import pdf_no_aptos_excursion


def _render_result_table(title: str, rows: list[dict]):
    st.markdown(f"### {title}")

    if not rows:
        st.info("No hay alumnos en esta categoría.")
        return

    table = []
    for i, r in enumerate(rows, start=1):
        table.append({
            "Nº": i,
            "Grupo": r["grupo"],
            "Alumno": r["alumno"],
            "Faltas": f'{r["total"]} ({r["graves"]} graves/muy graves)',
        })

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


def render_excursion_eligibility():
    st.subheader("🎒 No aptos para excursiones")

    # ==========================
    # FORMULARIO
    # ==========================
    with st.form("excursion_form"):
        actividad = st.text_input(
            "Nombre de la actividad",
            placeholder="Ej.: Excursión al Museo de Ciencias",
        )

        fecha_excursion = st.date_input(
            "Fecha de la excursión",
            value=date.today(),
            format="YYYY-MM-DD",
        )

        grupos = get_all_groups()
        grupos_sel = st.multiselect(
            "Grupos implicados",
            grupos,
        )

        calcular = st.form_submit_button("Calcular")

    if not calcular:
        return

    if not actividad.strip():
        st.error("Debes indicar el nombre de la actividad.")
        return

    if not grupos_sel:
        st.error("Debes seleccionar al menos un grupo.")
        return

    # ==========================
    # CÁLCULO
    # ==========================
    sancionados, amnistiables = get_excursion_eligibility(
        fecha_excursion=fecha_excursion.isoformat(),
        grupos=grupos_sel,
    )

    # Periodo exacto (mes anterior)
    fecha_desde = fecha_excursion - relativedelta(months=1)
    fecha_hasta = fecha_excursion - relativedelta(days=1)

    # Ordenación final
    sancionados.sort(key=lambda x: (x["grupo"], x["alumno"]))
    amnistiables.sort(key=lambda x: (x["grupo"], x["alumno"]))

    # ==========================
    # RESULTADOS
    # ==========================
    st.divider()

    st.markdown(f"## 📄 Actividad: **{actividad}**")
    st.caption(
        f"Periodo analizado: "
        f"{fecha_desde.strftime('%d/%m/%Y')} – {fecha_hasta.strftime('%d/%m/%Y')}"
    )

    st.divider()

    # ---- SANCIONADOS ----
    _render_result_table("🔴 Sancionados (no aptos)", sancionados)

    # ---- PDF ----
    if sancionados:
        pdf_bytes = pdf_no_aptos_excursion(
            rows=sancionados,
            actividad=actividad,
            fecha_excursion=fecha_excursion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            logo_path=Path("logo.png"),  # usa None si aún no tienes logo
        )

        st.download_button(
            "📄 Descargar PDF (No aptos para excursión)",
            data=pdf_bytes,
            file_name=f"no_aptos_{actividad.replace(' ', '_')}_{fecha_excursion.isoformat()}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.divider()

    # ---- AMNISTIABLES ----
    _render_result_table("🟡 Posibles amnistiados", amnistiables)
