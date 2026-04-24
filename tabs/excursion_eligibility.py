# tabs/excursion_eligibility.py
import streamlit as st
from datetime import date

from db.incidents import get_excursion_eligibility
from db.students import get_all_groups


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

    # Ordenación final garantizada (por seguridad)
    sancionados.sort(key=lambda x: (x["grupo"], x["alumno"]))
    amnistiables.sort(key=lambda x: (x["grupo"], x["alumno"]))

    # ==========================
    # RESULTADOS
    # ==========================
    st.divider()

    st.markdown(f"## 📄 Actividad: **{actividad}**")
    st.caption(
        f"Periodo analizado: "
        f"{(fecha_excursion.replace(day=fecha_excursion.day) )} (mes anterior a la excursión)"
    )

    st.divider()

    _render_result_table("🔴 Sancionados (no aptos)", sancionados)

    st.divider()

    _render_result_table("🟡 Posibles amnistiados", amnistiables)
