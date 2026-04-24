# tabs/student_analysis.py
import streamlit as st

from db.incidents import get_incidents, count_open_incidents
from db.students import get_all_students
from utils.enums import GRAVEDAD_MUY_GRAVE


def render_student_analysis(user: dict):
    st.subheader("🧒 Análisis por alumno")

    # -------------------------------
    # Selección de alumno
    # -------------------------------
    alumnos = get_all_students()
    if not alumnos:
        st.info("No hay alumnos registrados.")
        return

    alumno_sel = st.selectbox("Alumno", alumnos)

    st.divider()

    # -------------------------------
    # Filtro por fechas
    # -------------------------------
    c1, c2 = st.columns(2)

    fecha_desde = c1.date_input(
        "Desde",
        value=None,
        format="YYYY-MM-DD",
        key="student_analysis_fecha_desde",
    )

    fecha_hasta = c2.date_input(
        "Hasta",
        value=None,
        format="YYYY-MM-DD",
        key="student_analysis_fecha_hasta",
    )

    fecha_desde_str = fecha_desde.isoformat() if fecha_desde else None
    fecha_hasta_str = fecha_hasta.isoformat() if fecha_hasta else None

    # -------------------------------
    # Carga de incidencias
    # -------------------------------
    rows = get_incidents(
        mode="all",
        alumno=alumno_sel,  
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str,
    )

    if not rows:
        st.info("Este alumno no tiene incidencias registradas.")
        return

    # -------------------------------
    # KPIs simples
    # -------------------------------
    total = len(rows)
    abiertas = sum(1 for r in rows if r[8] != "cerrado")
    muy_graves = sum(1 for r in rows if r[6] == GRAVEDAD_MUY_GRAVE)

    c1, c2, c3 = st.columns(3)

    c1.metric("Total incidencias", total)
    c2.metric("Abiertas", abiertas)
    c3.metric("Muy graves", muy_graves)

    st.divider()

    # -------------------------------
    # Historial cronológico
    # -------------------------------
    st.markdown("### 📋 Historial")

    for r in rows:
        (
            _id,
            fecha,
            hora,
            grupo,
            _alumno,
            descripcion,
            gravedad_ini,
            gravedad_fin,
            estado,
            profesor,
        ) = r

        estado_txt = "🟢 Abierta" if estado != "cerrado" else "✅ Cerrada"
        gravedad_txt = gravedad_fin or gravedad_ini

        with st.expander(f"{fecha} · {grupo} · {gravedad_txt} · {estado_txt}"):
            st.markdown(
                f"""
                **Profesor:** {profesor}  
                **Gravedad inicial:** {gravedad_ini}  
                **Gravedad final:** {gravedad_fin or '—'}  

                **Descripción:**  
                {descripcion}
                """
            )
