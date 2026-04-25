# tabs/teacher_analysis.py
import streamlit as st
from pathlib import Path
from config import LOGO_PATH

from db.incidents import get_incidents
from db.users import get_all_teachers   # o como obtengas profesores
from utils.pdf_teacher_history import pdf_teacher_history


def render_teacher_analysis(user: dict):
    st.subheader("👨‍🏫 Análisis por profesor")

    # -------------------------------
    # Selección de profesor
    # -------------------------------
    profesores = get_all_teachers()
    if not profesores:
        st.info("No hay profesores registrados.")
        return

    profesor_sel = st.selectbox("Profesor", profesores)

    st.divider()

    # -------------------------------
    # Filtro por fechas
    # -------------------------------
    c1, c2 = st.columns(2)

    fecha_desde = c1.date_input("Desde", value=None)
    fecha_hasta = c2.date_input("Hasta", value=None)

    fecha_desde_str = fecha_desde.isoformat() if fecha_desde else None
    fecha_hasta_str = fecha_hasta.isoformat() if fecha_hasta else None

    # -------------------------------
    # Carga de incidencias
    # -------------------------------
    rows = get_incidents(
        mode="all",
        profesor_id=None,          # o teacher_id si lo usas
        profesor=profesor_sel,     # según tu modelo
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str,
    )

    if not rows:
        st.info("Este profesor no tiene incidencias registradas.")
        return

    st.divider()
    st.markdown("### 📋 Historial")

    # -------------------------------
    # Mostrar historial
    # -------------------------------
    for r in rows:
        (
            _id,
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            profesor,
        ) = r

        gravedad_txt = grav_fin or grav_ini

        with st.expander(f"{fecha} · {alumno} ({grupo}) · {gravedad_txt}"):
            st.write(descripcion)

    # -------------------------------
    # Preparar datos PDF
    # -------------------------------
    rows_formateadas = []
    for r in rows:
        (
            _id,
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            grav_ini,
            grav_fin,
            estado,
            profesor,
        ) = r

        rows_formateadas.append({
            "fecha": fecha,
            "hora": hora or "",
            "alumno": alumno,
            "grupo": grupo,
            "gravedad": grav_fin or grav_ini,
            "descripcion": descripcion,
        })

    fecha_desde_pdf = fecha_desde or min(r["fecha"] for r in rows_formateadas)
    fecha_hasta_pdf = fecha_hasta or max(r["fecha"] for r in rows_formateadas)

    st.divider()

    pdf_bytes = pdf_teacher_history(
        rows=rows_formateadas,
        profesor=profesor_sel,
        fecha_desde=fecha_desde_pdf,
        fecha_hasta=fecha_hasta_pdf,
        logo_path=LOGO_PATH,
    )

    st.download_button(
        "📄 Descargar PDF (Historial del profesor)",
        data=pdf_bytes,
        file_name=f"historial_profesor_{profesor_sel.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
