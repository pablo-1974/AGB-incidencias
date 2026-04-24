# tabs/admin.py
import streamlit as st
import pandas as pd

from tabs.incidents_list import render_incidents_list
from tabs.incidents_create import render_incident_create
from tabs.incidents_close import render_incidents_close
from tabs.rankings import render_rankings
from tabs.student_analysis import render_student_analysis
from tabs.excursion_eligibility import render_excursion_eligibility

from db.incidents import (
    count_open_incidents,
    count_open_very_serious_incidents,
    count_incidents_created_this_week,
    count_incidents_closed_this_week,
)

from db.students import (
    get_all_students,
    upsert_student_by_name,
    change_student_group,
)

def _render_dashboard_admin():
    """
    Dashboard (home) de Administración.
    Reutiliza exactamente los KPIs de Jefatura.
    """

    # ==========================
    # KPIs
    # ==========================
    pending = count_open_incidents()
    very_serious = count_open_very_serious_incidents()
    created_week = count_incidents_created_this_week()
    closed_week = count_incidents_closed_this_week()

    # ==========================
    # AVISO / ESTADO GENERAL
    # ==========================
    if pending == 0:
        st.success("✅ No hay incidencias pendientes.")
    elif very_serious > 0:
        st.error("🚨 Hay incidencias muy graves pendientes de revisar.")
    else:
        st.warning("⚠️ Hay incidencias pendientes de revisar.")

    # ==========================
    # KPIs VISUALES
    # ==========================
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("📬 Pendientes", pending)

    with c2:
        st.metric("🚨 Muy graves", very_serious)

    with c3:
        st.metric("📅 Esta semana", created_week)

    with c4:
        st.metric("✅ Cerradas", closed_week)

    # ==========================
    # BOTÓN DE ACCIÓN
    # ==========================
    if pending > 0:
        if st.button("✅ Revisar incidencias pendientes", use_container_width=True):
            st.session_state["admin_focus"] = "close"


def render_admin(user: dict):
    st.subheader("🛠️ Administración")

    # ==========================
    # DASHBOARD (HOME)
    # ==========================
    _render_dashboard_admin()

    st.divider()

    # ==========================
    # GESTIÓN DE ALUMNOS (SOLO ADMIN)
    # ==========================
    st.subheader("🎓 Gestión de alumnos")

    tabs_alumnos = st.tabs(
        ["📥 Importar alumnos", "🔁 Cambiar grupo", "➕ Añadir alumno"]
    )

    # --------------------------------------------------
    # IMPORTAR ALUMNOS DESDE EXCEL
    # --------------------------------------------------
    with tabs_alumnos[0]:
        st.markdown("### 📥 Importar alumnos desde Excel")
        st.caption("Columnas obligatorias: **Alumno** y **Grupo**")

        file = st.file_uploader(
            "Selecciona archivo Excel",
            type=["xlsx"],
            key="admin_import_students",
        )

        if file:
            df = pd.read_excel(file)

            if not {"Alumno", "Grupo"}.issubset(df.columns):
                st.error("❌ El Excel debe tener las columnas: Alumno y Grupo")
            else:
                added = updated = unchanged = 0

                for _, row in df.iterrows():
                    alumno = str(row["Alumno"]).strip()
                    grupo = str(row["Grupo"]).strip()
                
                    if not alumno or not grupo:
                        continue
                
                    result = upsert_student_by_name(
                        alumno=alumno,
                        grupo=grupo,
                    )
                
                    if result == "added":
                        added += 1
                    elif result == "updated":
                        updated += 1
                    else:
                        unchanged += 1

                st.success(
                    f"✅ Importación completada\n\n"
                    f"➕ Nuevos alumnos: {added}\n"
                    f"🔁 Grupo actualizado: {updated}\n"
                    f"✔️ Sin cambios: {unchanged}"
                )
                st.info("ℹ️ El historial de incidencias NO se ha modificado.")

    # --------------------------------------------------
    # CAMBIAR GRUPO DE ALUMNO
    # --------------------------------------------------
    with tabs_alumnos[1]:
        st.markdown("### 🔁 Cambiar grupo de un alumno")

        alumnos = get_all_students()
        if not alumnos:
            st.info("No hay alumnos registrados.")
        else:
            alumno_sel = st.selectbox("Alumno", alumnos, key="admin_change_group_student")
            nuevo_grupo = st.text_input("Nuevo grupo", key="admin_change_group")

            if st.button("Actualizar grupo", key="admin_change_group_btn"):
                if not nuevo_grupo.strip():
                    st.error("Debes indicar un nuevo grupo.")
                else:
                    ok = change_student_group(
                        alumno=alumno_sel,
                        new_grupo=nuevo_grupo,
                    )
                    if ok:
                        st.success("✅ Grupo actualizado correctamente.")
                        st.rerun()
                    else:
                        st.error("No se pudo actualizar el grupo.")

    # --------------------------------------------------
    # AÑADIR ALUMNO MANUALMENTE
    # --------------------------------------------------
    with tabs_alumnos[2]:
        st.markdown("### ➕ Añadir alumno manualmente")

        alumno = st.text_input("Alumno", key="admin_add_student_name")
        grupo = st.text_input("Grupo", key="admin_add_student_group")

        if st.button("Añadir alumno", key="admin_add_student_btn"):
            try:
                result = upsert_student_by_name(
                    alumno=alumno,
                    grupo=grupo,
                )
                if result == "added":
                    st.success("✅ Alumno añadido correctamente.")
                elif result == "updated":
                    st.warning("ℹ️ El alumno ya existía. Se ha actualizado el grupo.")
                else:
                    st.info("ℹ️ El alumno ya existía y no se ha modificado.")
            except ValueError as e:
                st.error(str(e))

    st.divider()

    # ==========================
    # RANKINGS
    # ==========================
    st.subheader("📊 Rankings")
    render_rankings(user["role"])
    
    st.divider()
    
    
    # ==========================
    # ANÁLISIS ALUMNO
    # ==========================
    
    st.subheader("🧒 Análisis por alumno")
    render_student_analysis(user)
    
    st.divider()
    

    # ==========================
    # NAVEGACIÓN DIRECTA (BOTÓN)
    # ==========================
    if st.session_state.get("admin_focus") == "close":
        st.session_state.pop("admin_focus", None)
        render_incidents_close(user)
        return

    # ==========================
    # TABS NORMALES
    # ==========================
    tabs = st.tabs(
        ["📄 Incidencias", "➕ Nueva incidencia", "✅ Cerrar incidencia"]
    )

    with tabs[0]:
        render_incidents_list(user, mode="all")

    with tabs[1]:
        render_incident_create(user)

    with tabs[2]:
        render_incidents_close(user)
