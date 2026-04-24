# tabs/incidents_list.py
import streamlit as st
import pandas as pd
from db.connection import get_db


def render_incidents_list(user: dict, mode: str = "own"):
    """
    Lista incidencias con filtros avanzados.

    mode:
      - "own" -> solo incidencias del usuario
      - "all" -> todas las incidencias (aparece filtro Profesor)
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
    cols = st.columns(6 if mode == "all" else 5)
    col = 0

    if mode == "all":
        with cols[col]:
            profesor_sel = st.selectbox(
                "Profesor",
                ["— Todos —"] + profesores,
                format_func=lambda x: x if isinstance(x, str) else x[1],
            )
        col += 1
    else:
        profesor_sel = None

    with cols[col]:
        grupo_sel = st.selectbox("Grupo", ["— Todos —"] + grupos)
    col += 1

    with cols[col]:
        alumno_sel = st.selectbox("Alumno", ["— Todos —"] + alumnos)
    col += 1

    with cols[col]:
        estado_sel = st.selectbox("Estado", ["— Todos —"] + estados)
    col += 1

    with cols[col]:
        gravedad_sel = st.selectbox("Gravedad", ["— Todas —"] + gravedades)
    col += 1

    with cols[col]:
        fecha_sel = st.date_input("Fecha", value=None)

    # =========================
    # WHERE DINÁMICO
    # =========================
    where = []
    params = []

    if mode == "own":
        where.append("teacher_id = %s")
        params.append(user["id"])

    if mode == "all" and profesor_sel not in (None, "— Todos —"):
        where.append("teacher_id = %s")
        params.append(profesor_sel[0])

    if grupo_sel != "— Todos —":
        where.append("grupo = %s")
        params.append(grupo_sel)

    if alumno_sel != "— Todos —":
        where.append("alumno = %s")
        params.append(alumno_sel)

    if estado_sel != "— Todos —":
        where.append("estado = %s")
        params.append(estado_sel)

    if gravedad_sel != "— Todas —":
        where.append("gravedad_inicial = %s")
        params.append(gravedad_sel)

    if fecha_sel:
        where.append("fecha = %s")
        params.append(fecha_sel.isoformat())

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    # =========================
    # CONSULTA FINAL
    # =========================
    query = f"""
        SELECT
            fecha,
            hora,
            grupo,
            alumno,
            descripcion,
            gravedad_inicial,
            gravedad_final,
            estado,
            teacher_name
        FROM incidents
        {where_sql}
        ORDER BY id DESC
    """

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

    except Exception as e:
        st.error("❌ Error al cargar incidencias.")
        st.exception(e)
        return

    if not rows:
        st.info("No hay incidencias con esos filtros.")
        return

    df = pd.DataFrame(
        rows,
        columns=[
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
