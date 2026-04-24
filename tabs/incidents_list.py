# tabs/incidents_list.py
import streamlit as st
import pandas as pd

from db.connection import get_db
from db.incidents import get_incidents


def render_incidents_list(user: dict, mode: str = "own"):
    """
    Lista incidencias con filtros avanzados y rango de fechas.
    UI pura. SQL delegado a db/incidents.py.
    """

    st.subheader("📄 Incidencias")

    # =========================
    # CARGA DE OPCIONES
    # =========================
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT grupo FROM incidents ORDER BY grupo")
                grupos = [r[0] for r in cur.fetchall() if r[0]]

                cur.execute("SELECT DISTINCT alumno FROM incidents ORDER BY alumno")
                alumnos = [r[0] for r in cur.fetchall() if r[0]]

                cur.execute("SELECT DISTINCT estado FROM incidents ORDER BY estado")
                estados = [r[0] for r in cur.fetchall() if r[0]]

                cur.execute(
                    "SELECT DISTINCT gravedad_inicial FROM incidents ORDER BY gravedad_inicial"
                )
                gravedades = [r[0] for r in cur.fetchall() if r[0]]

                profesores = []
                if mode == "all":
                    cur.execute(
                        "SELECT DISTINCT teacher_id, teacher_name FROM incidents ORDER BY teacher_name"
                    )
                    profesores = [(r[0], r[1]) for r in cur.fetchall() if r[1]]

    except Exception as e:
        st.error("❌ Error al cargar filtros.")
        st.exception(e)
        return

    # =========================
    # FILTROS
    # =========================
    cols = st.columns(7 if mode == "all" else 6)
    i = 0

    if mode == "all":
        with cols[i]:
            profesor_sel = st.selectbox(
                "Profesor",
                ["— Todos —"] + profesores,
                format_func=lambda x: x if isinstance(x, str) else x[1],
            )
        i += 1
    else:
        profesor_sel = None

    with cols[i]:
        grupo_sel = st.selectbox("Grupo", ["— Todos —"] + grupos)
    i += 1

    with cols[i]:
        alumno_sel = st.selectbox("Alumno", ["— Todos —"] + alumnos)
    i += 1

    with cols[i]:
        estado_sel = st.selectbox("Estado", ["— Todos —"] + estados)
    i += 1

    with cols[i]:
        gravedad_sel = st.selectbox("Gravedad", ["— Todas —"] + gravedades)
    i += 1

    with cols[i]:
        fecha_desde = st.date_input("Desde", value=None)

    with cols[i + 1]:
        fecha_hasta = st.date_input("Hasta", value=None)

    # =========================
    # LLAMADA A LA CAPA DB
    # =========================
    rows = get_incidents(
        mode=mode,
        user_id=user["id"],
        profesor_id=(
            profesor_sel[0]
            if mode == "all" and profesor_sel not in (None, "— Todos —")
            else None
        ),
        grupo=None if grupo_sel == "— Todos —" else grupo_sel,
        alumno=None if alumno_sel == "— Todos —" else alumno_sel,
        estado=None if estado_sel == "— Todos —" else estado_sel,
        gravedad=None if gravedad_sel == "— Todas —" else gravedad_sel,
        fecha_desde=fecha_desde.isoformat() if fecha_desde else None,
        fecha_hasta=fecha_hasta.isoformat() if fecha_hasta else None,
    )

    if not rows:
        st.info("No hay incidencias con esos filtros.")
        return

    # =========================
    # DATAFRAME
    # =========================
    df = pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Fecha",
            "Hora",
            "Grupo",
            "Alumno",
            "Descripción",
            "Gravedad inicial",
            "Gravedad final",
            "Estado",
            "Profesor",
        ],
    )

    st.dataframe(df, use_container_width=True)
