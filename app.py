# ===================== app.py =====================
# Ejecuta: streamlit run app.py
# Requisitos: streamlit, pandas, openpyxl, reportlab
# Postgres (Neon): añade psycopg[binary] e indica DATABASE_URL (con ?sslmode=require)
# Render (Web Service): streamlit run app.py --server.port $PORT --server.address 0.0.0.0

# ========== BLOQUE 1/7: Imports, Config, Compat BD, Seguridad ==========

import os
import base64
import hashlib
import hmac
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from io import BytesIO

import streamlit as st
import pandas as pd

# ===== Soporte PDF =====
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

# =========================
# CONFIG / CONSTANTES
# =========================
APP_TITLE = "Partes de Incidencias. IES Antonio García Bellido"

HERE = Path(__file__).parent.resolve()
DB_PATH = HERE / "incidencias.db"
ALUMNOS_XLSX = HERE / "alumnos.xlsx"  # columnas: Grupo, Alumno
FRANJAS = ["1ª", "2ª", "3ª", "Recreo", "4ª", "5ª", "6ª"]

# Motor de BD: SQLite por defecto; si hay DATABASE_URL (postgres) se usa Postgres (psycopg)
DB_URL = os.getenv("DATABASE_URL", "").strip()
DB_ENGINE = "sqlite" if DB_URL == "" else ("postgres" if DB_URL.startswith("postgres") else "sqlite")

if DB_ENGINE == "postgres":
    try:
        import psycopg  # psycopg3
    except Exception as ex:
        raise RuntimeError(
            "Se requiere 'psycopg[binary]' para usar PostgreSQL (Neon). "
            "Instala: pip install 'psycopg[binary]'"
        ) from ex

# =========================
# CAPA DE COMPATIBILIDAD BD
# =========================
class SQLiteConn:
    def __init__(self, path: Path):
        self._conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA synchronous = NORMAL;")
        self._conn.row_factory = sqlite3.Row

    def cursor(self):
        return self._conn.cursor()

    def execute(self, sql, params=()):
        return self._conn.execute(sql, params or [])

    def executemany(self, sql, params_seq):
        return self._conn.executemany(sql, params_seq)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._conn.commit()
        self._conn.close()

class CursorShim:
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

class PostgresConn:
    def __init__(self, url: str):
        self._conn = psycopg.connect(self._ensure_sslmode(url),
                                     keepalives=1,
                                     keepalives_idle=30,
                                     keepalives_interval=10,
                                     keepalives_count=5)

    @staticmethod
    def _ensure_sslmode(url: str) -> str:
        if "sslmode=" in url:
            return url
        return url + ("?sslmode=require" if "?" not in url else "&sslmode=require")

    def cursor(self):
        return self._conn.cursor()

    def _prep_sql(self, sql: str) -> str:
        return sql.replace("?", "%s")

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(self._prep_sql(sql), params or [])
        return CursorShim(cur)

    def executemany(self, sql, params_seq):
        cur = self._conn.cursor()
        cur.executemany(self._prep_sql(sql), params_seq)
        return CursorShim(cur)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._conn.commit()
        self._conn.close()

@contextmanager
def get_conn():
    if DB_ENGINE == "sqlite":
        with SQLiteConn(DB_PATH) as conn:
            yield conn
    else:
        with PostgresConn(DB_URL) as conn:
            yield conn

# =========================
# SEGURIDAD: HASH DE CONTRASEÑA (PBKDF2)
# =========================
PBKDF2_ITER = 200_000

def hash_password(pwd: str) -> str:
    """Devuelve 'salt_b64$hash_b64' usando PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, PBKDF2_ITER)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def verify_password(pwd: str, stored: str) -> bool:
    try:
        salt_b64, hash_b64 = stored.split("$", 1)
        salt = base64.b64decode(salt_b64)
        dk_stored = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, PBKDF2_ITER)
        return hmac.compare_digest(dk, dk_stored)
    except Exception:
        return False

# ========== BLOQUE 2/7: Init BD, Usuarios, Alumnos ==========

def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        # USERS
        if DB_ENGINE == "sqlite":
            c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK(role IN ('profesor','jefe','director','convivencia')),
                password_hash TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """)
        else:
            c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK(role IN ('profesor','jefe','director','convivencia')),
                password_hash TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """)

        # STUDENTS
        if DB_ENGINE == "sqlite":
            c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo TEXT NOT NULL,
                alumno TEXT NOT NULL
            )
            """)
        else:
            c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                grupo TEXT NOT NULL,
                alumno TEXT NOT NULL
            )
            """)

        # INCIDENTS
        if DB_ENGINE == "sqlite":
            c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                teacher_name TEXT NOT NULL,
                grupo TEXT NOT NULL,
                alumno TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                gravedad_inicial TEXT NOT NULL CHECK(gravedad_inicial IN ('leve','grave','muy grave')),
                gravedad_final TEXT,
                estado TEXT NOT NULL CHECK(estado IN ('pendiente','cerrado')),
                created_at TEXT NOT NULL,
                reviewed_by INTEGER,
                reviewed_by_name TEXT,
                closed_at TEXT
            )
            """)
        else:
            c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER NOT NULL,
                teacher_name TEXT NOT NULL,
                grupo TEXT NOT NULL,
                alumno TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                gravedad_inicial TEXT NOT NULL CHECK(gravedad_inicial IN ('leve','grave','muy grave')),
                gravedad_final TEXT,
                estado TEXT NOT NULL CHECK(estado IN ('pendiente','cerrado')),
                created_at TEXT NOT NULL,
                reviewed_by INTEGER,
                reviewed_by_name TEXT,
                closed_at TEXT
            )
            """)

        # Índices
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_estado_fecha ON incidents(estado, fecha)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_fecha ON incidents(fecha)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_grupo_alumno ON incidents(grupo, alumno)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_gravedad_final ON incidents(gravedad_final)")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_students_grupo_alumno ON students(grupo, alumno)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_teacher_fecha_estado ON incidents(teacher_id, fecha, estado)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_grupo_fecha ON incidents(grupo, fecha)")
        conn.commit()

        # --- Migración automática (solo SQLite) ---
        if DB_ENGINE == "sqlite":
            row = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
            if row and "CHECK(role IN ('profesor','jefe'))" in (row[0] or ""):
                c.execute("ALTER TABLE users RENAME TO users_backup")
                c.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        role TEXT NOT NULL CHECK(role IN ('profesor','jefe','director','convivencia')),
                        password_hash TEXT,
                        active INTEGER NOT NULL DEFAULT 1
                    )
                """)
                c.execute("INSERT INTO users(id,name,email,role,password_hash,active) SELECT id,name,email,role,password_hash,active FROM users_backup")
                c.execute("DROP TABLE users_backup")
                conn.commit()

def no_users_exist() -> bool:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0

# ---- USUARIOS ----
def create_user(name: str, email: str, role: str):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    role = (role or "").strip().lower()
    if not name or not email:
        return False, "Nombre y email obligatorios."
    if role not in ("profesor","jefe","director","convivencia"):
        return False, "Rol no válido."
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO users(name,email,role,password_hash,active) VALUES (?,?,?,?,1)",
                (name, email, role, None)
            )
            conn.commit()
            return True, "Usuario creado. Establecerá contraseña en su primer acceso."
        except Exception:
            return False, "Ese email ya existe."

def get_user_by_email(email: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,email,role,password_hash,active FROM users WHERE email=?",
            (email.lower(),)
        ).fetchone()

def get_user_by_name(name: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,email,role,password_hash,active FROM users WHERE name=?",
            (name,)
        ).fetchone()

def list_users():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,email,role,active,password_hash FROM users ORDER BY role DESC, name"
        ).fetchall()

def list_profesores():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id,name,email FROM users WHERE active=1 ORDER BY name"
        ).fetchall()

def list_profesor_names() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM users WHERE active=1 ORDER BY name").fetchall()
    return [r[0] for r in rows]

def set_user_password(user_id: int, raw_password: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(raw_password), user_id))
        conn.commit()

def set_user_active(user_id: int, active: bool):
    with get_conn() as conn:
        conn.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
        conn.commit()

def delete_user(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()

def set_user_role(user_id: int, new_role: str):
    if new_role not in ("profesor","jefe","director","convivencia"):
        return False, "Rol no válido."
    with get_conn() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        conn.commit()
    return True, "Rol actualizado correctamente."

def next_role(current: str) -> str:
    # Compatibilidad
    order = ["profesor", "jefe", "director", "convivencia"]
    try:
        i = order.index(current)
        return order[(i + 1) % len(order)]
    except ValueError:
        return "profesor"

# ---- PROFESORES DESDE EXCEL ----
def import_profesores_from_excel(df: pd.DataFrame) -> tuple[int,int]:
    cols = {c.strip().lower(): c for c in df.columns}
    nombre_col = cols.get("nombre") or cols.get("name")
    email_col  = cols.get("email")  or cols.get("correo")
    if not nombre_col or not email_col:
        raise ValueError("El Excel debe contener columnas 'Nombre' y 'Email'.")

    df2 = df[[nombre_col, email_col]].copy()
    df2.columns = ["Nombre","Email"]
    df2["Nombre"] = df2["Nombre"].astype(str).str.strip()
    df2["Email"]  = df2["Email"].astype(str).str.strip().str.lower()
    df2 = df2[(df2["Nombre"]!="") & (df2["Email"]!="")]

    ins, skip = 0, 0
    for _, row in df2.iterrows():
        ok, _ = create_user(row["Nombre"], row["Email"], "profesor")
        if ok: ins += 1
        else:  skip += 1
    return ins, skip

# ---- ALUMNOS ----

def insert_student(grupo: str, alumno: str) -> tuple[bool, str]:
    """Inserta alumno (grupo, alumno). Si existe, no falla."""
    grupo = (grupo or "").strip()
    alumno = (alumno or "").strip()
    if not grupo or not alumno:
        return False, "Grupo y Alumno son obligatorios."

    sql_sqlite = "INSERT OR IGNORE INTO students(grupo, alumno) VALUES (?,?)"
    sql_pg = "INSERT INTO students(grupo, alumno) VALUES (?,?) ON CONFLICT (grupo, alumno) DO NOTHING"

    with get_conn() as conn:
        try:
            if DB_ENGINE == "sqlite":
                conn.execute(sql_sqlite, (grupo, alumno))
            else:
                conn.execute(sql_pg, (grupo, alumno))
            conn.commit()
            return True, "Alumno insertado (o ya existente)."
        except Exception as ex:
            return False, f"No se pudo insertar: {ex}"

def delete_student(grupo: str, alumno: str) -> tuple[bool, str]:
    """
    Elimina un alumno del maestro 'students'. No borra partes de 'incidents'.
    Devuelve (ok, mensaje). Si no existe, no falla y lo indica.
    """
    grupo = (grupo or "").strip()
    alumno = (alumno or "").strip()
    if not grupo or not alumno:
        return False, "Debes indicar Grupo y Alumno."

    # Comprobación opcional: partes asociados (solo para informar)
    with get_conn() as conn:
        try:
            cnt_parts = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE grupo=? AND alumno=?",
                (grupo, alumno)
            ).fetchone()[0]

            # Intentar borrar del maestro
            cur = conn.execute(
                "DELETE FROM students WHERE grupo=? AND alumno=?",
                (grupo, alumno)
            )
            conn.commit()

            if cur.rowcount == 0:
                return False, "No se encontró ese alumno en el maestro."

            if cnt_parts > 0:
                return True, f"Alumno eliminado del maestro. Nota: existen {cnt_parts} parte(s) asociados que NO se han borrado."
            else:
                return True, "Alumno eliminado del maestro."

        except Exception as ex:
            return False, f"No se pudo eliminar: {ex}"

def import_alumnos_df_to_db(df: pd.DataFrame, mode: str = "merge"):
    """
    Importa alumnos desde un DataFrame.
    mode:
      - 'replace' -> elimina todo y vuelve a cargar
      - 'merge'   -> inserta nuevos sin borrar existentes (recomendado)
    """
    if not {"Grupo","Alumno"}.issubset(df.columns):
        raise ValueError("El Excel de alumnos debe tener columnas: 'Grupo' y 'Alumno'.")
    df2 = df[["Grupo","Alumno"]].copy()
    df2["Grupo"] = df2["Grupo"].astype(str).str.strip()
    df2["Alumno"] = df2["Alumno"].astype(str).str.strip()
    df2 = df2[(df2["Grupo"]!="") & (df2["Alumno"]!="")].drop_duplicates()

    with get_conn() as conn:
        if mode == "replace":
            conn.execute("DELETE FROM students")
            conn.executemany("INSERT INTO students(grupo, alumno) VALUES (?,?)", list(map(tuple, df2.values)))
        else:
            if DB_ENGINE == "sqlite":
                conn.executemany("INSERT OR IGNORE INTO students(grupo, alumno) VALUES (?,?)", list(map(tuple, df2.values)))
            else:
                conn.executemany(
                    "INSERT INTO students(grupo, alumno) VALUES (?,?) ON CONFLICT (grupo, alumno) DO NOTHING",
                    list(map(tuple, df2.values))
                )
        conn.commit()

def load_alumnos_from_excel_if_exists():
    if ALUMNOS_XLSX.exists():
        df = pd.read_excel(ALUMNOS_XLSX, engine="openpyxl")
        import_alumnos_df_to_db(df, mode="merge")

def list_grupos():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT grupo FROM students ORDER BY grupo").fetchall()
    return [r[0] for r in rows]

def list_alumnos_by_grupo(grupo: str):
    with get_conn() as conn:
        rows = conn.execute("SELECT alumno FROM students WHERE grupo=? ORDER BY alumno", (grupo,)).fetchall()
    return [r[0] for r in rows]

# ========== BLOQUE 3/7: Incidencias, Consultas, Ranking, No Aptos, UI ==========

# ---- INCIDENCIAS ----
def create_incident(teacher_id: int, teacher_name: str, grupo: str, alumno: str,
                    fecha: date, franja: str, descripcion: str, gravedad_inicial: str):
    # Validación de campos
    if not (teacher_id and teacher_name and grupo and alumno and descripcion and gravedad_inicial and fecha and franja):
        return False, "Todos los campos del parte son obligatorios."
    if gravedad_inicial not in ("leve","grave","muy grave"):
        return False, "Gravedad inicial inválida."
    if franja not in FRANJAS:
        return False, "Franja horaria inválida."

    # 🚫 Bloqueo de FECHA FUTURA (servidor)
    try:
        if isinstance(fecha, datetime):
            fecha_d = fecha.date()
        else:
            fecha_d = fecha
        if fecha_d > date.today():
            return False, "No se permiten partes con fecha futura."
    except Exception:
        return False, "Fecha inválida."

    with get_conn() as conn:
        conn.execute("""
        INSERT INTO incidents(teacher_id, teacher_name, grupo, alumno, fecha, hora,
                              descripcion, gravedad_inicial, gravedad_final,
                              estado, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (teacher_id, teacher_name, grupo, alumno,
              fecha_d.isoformat(), franja,
              descripcion.strip(), gravedad_inicial, None,
              "pendiente", datetime.now(timezone.utc).isoformat()))
        conn.commit()
    return True, "Parte creado y enviado a Jefatura para revisión."

def list_pending_incidents():
    with get_conn() as conn:
        return conn.execute("""
        SELECT id, teacher_name, grupo, alumno, fecha, hora, descripcion, gravedad_inicial, created_at
        FROM incidents
        WHERE estado='pendiente'
        ORDER BY created_at DESC
        """).fetchall()

def close_incident(incident_id: int, gravedad_final: str, reviewer_id: int, reviewer_name: str):
    if gravedad_final not in ("leve","grave","muy grave"):
        return False, "Debes valorar la gravedad antes de cerrar el parte."
    with get_conn() as conn:
        conn.execute("""
        UPDATE incidents
        SET gravedad_final=?, estado='cerrado', reviewed_by=?, reviewed_by_name=?, closed_at=?
        WHERE id=?
        """, (gravedad_final, reviewer_id, reviewer_name, datetime.now(timezone.utc).isoformat(), incident_id))
        conn.commit()
    return True, "Parte cerrado correctamente."

def filter_closed_incidents(start: date|None, end: date|None, grupo: str|None, alumno: str|None):
    query = "SELECT id,teacher_name,grupo,alumno,fecha,hora,descripcion,gravedad_inicial,gravedad_final,created_at,closed_at FROM incidents WHERE estado='cerrado'"
    params = []
    if start:
        query += " AND fecha >= ?"; params.append(start.isoformat())
    if end:
        query += " AND fecha <= ?"; params.append(end.isoformat())
    if grupo and grupo != "Todos":
        query += " AND grupo = ?"; params.append(grupo)
    if alumno and alumno != "Todos":
        query += " AND alumno = ?"; params.append(alumno)
    query += " ORDER BY fecha DESC, hora DESC"
    with get_conn() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    cols = ["ID","Profesor","Grupo","Alumno","Fecha","Hora","Descripción","Gravedad inicial","Gravedad final","Creado","Cerrado"]
    return pd.DataFrame(rows, columns=cols)

def filter_teacher_incidents(
    teacher_id: int,
    start: date | None,
    end: date | None,
    estado: str = "Todos",
    grupo: str | None = "Todos",
    alumno: str | None = "Todos",
) -> pd.DataFrame:
    """
    Devuelve un DataFrame con los partes emitidos por un profesor (teacher_id) en el rango de fechas.
    Permite filtrar por estado, grupo y alumno.
    Columnas: ID, Fecha, Franja, Grupo, Alumno, Estado, Gravedad inicial, Gravedad final, Profesor, Descripción, Creado, Cerrado
    """
    query = """
        SELECT id, fecha, hora, grupo, alumno, estado,
               gravedad_inicial, gravedad_final, teacher_name, descripcion,
               created_at, closed_at
        FROM incidents
        WHERE teacher_id=?
    """
    params = [teacher_id]

    if start:
        query += " AND fecha >= ?"
        params.append(start.isoformat())
    if end:
        query += " AND fecha <= ?"
        params.append(end.isoformat())
    if estado and estado in ("pendiente", "cerrado"):
        query += " AND estado = ?"
        params.append(estado)
    if grupo and grupo != "Todos":
        query += " AND grupo = ?"
        params.append(grupo)
    if alumno and alumno != "Todos":
        query += " AND alumno = ?"
        params.append(alumno)

    with get_conn() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    cols = ["ID","Fecha","Franja","Grupo","Alumno","Estado",
            "Gravedad inicial","Gravedad final","Profesor","Descripción","Creado","Cerrado"]
    df = pd.DataFrame(rows, columns=cols)
    return df

# =========================
# APOYO: EXCURSIONES / RANKING
# =========================
def excursion_banlist(activity_date: date, grupo_filtro: str = "Todos", lookback_days: int = 30):
    start = activity_date - timedelta(days=lookback_days)
    graves = ("grave","muy grave")

    where_30 = ["estado='cerrado'", "fecha BETWEEN ? AND ?", f"gravedad_final IN ({','.join('?'*len(graves))})"]
    params_30 = [start.isoformat(), activity_date.isoformat(), *graves]
    if grupo_filtro and grupo_filtro != "Todos":
        where_30.append("grupo = ?")
        params_30.append(grupo_filtro)

    sql_30 = f"""
        SELECT grupo, alumno, COUNT(*) as cnt
        FROM incidents
        WHERE {' AND '.join(where_30)}
        GROUP BY grupo, alumno
    """

    where_tot = []
    params_tot = []
    if grupo_filtro and grupo_filtro != "Todos":
        where_tot.append("grupo = ?")
        params_tot.append(grupo_filtro)
    sql_tot = "SELECT grupo, alumno, COUNT(*) as cnt FROM incidents"
    if where_tot:
        sql_tot += " WHERE " + " AND ".join(where_tot)
    sql_tot += " GROUP BY grupo, alumno"

    with get_conn() as conn:
        rows_30d = conn.execute(sql_30, tuple(params_30)).fetchall()
        rows_tot = conn.execute(sql_tot, tuple(params_tot)).fetchall()

    df_30 = pd.DataFrame(rows_30d, columns=["Grupo","Alumno","Partes_30d"])
    df_tot = pd.DataFrame(rows_tot, columns=["Grupo","Alumno","Partes_totales"])

    if df_30.empty:
        return pd.DataFrame(columns=["Grupo","Alumno","Partes_30d","Partes_totales"])

    df = df_30.merge(df_tot, on=["Grupo","Alumno"], how="left").fillna({"Partes_totales": 0})
    df["Partes_30d"] = df["Partes_30d"].astype(int)
    df["Partes_totales"] = df["Partes_totales"].astype(int)
    return df.sort_values(["Grupo","Alumno"]).reset_index(drop=True)

def ranking_disruptivos(start: date, end: date, grupo_filtro: str = "Todos",
                        solo_cerrados: bool = True, ponderar_gravedad: bool = True) -> pd.DataFrame:
    where = []
    params = []
    if solo_cerrados:
        where.append("estado='cerrado'")
    where.append("fecha BETWEEN ? AND ?")
    params.extend([start.isoformat(), end.isoformat()])
    if grupo_filtro and grupo_filtro != "Todos":
        where.append("grupo = ?")
        params.append(grupo_filtro)

    where_sql = " AND ".join(where)
    sql = f"""
        SELECT grupo, alumno, gravedad_final, COUNT(*) as cnt
        FROM incidents
        WHERE {where_sql}
        GROUP BY grupo, alumno, gravedad_final
    """
    with get_conn() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()

    if not rows:
        cols = ["Rank","Grupo","Alumno","Partes"]
        if ponderar_gravedad:
            cols.append("Puntos")
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows, columns=["Grupo","Alumno","Gravedad","Cnt"])
    total = df.groupby(["Grupo","Alumno"])["Cnt"].sum().reset_index().rename(columns={"Cnt":"Partes"})

    if ponderar_gravedad:
        peso = {"leve":1, "grave":2, "muy grave":3, None:1}
        df["Peso"] = df["Gravedad"].map(lambda g: peso.get(g, 1))
        df["Pts"] = df["Cnt"] * df["Peso"]
        puntos = df.groupby(["Grupo","Alumno"])["Pts"].sum().reset_index().rename(columns={"Pts":"Puntos"})
        out = total.merge(puntos, on=["Grupo","Alumno"], how="left").fillna({"Puntos":0})
        out["Puntos"] = out["Puntos"].astype(int)
        out = out.sort_values(["Puntos","Partes","Grupo","Alumno"], ascending=[False,False,True,True])
    else:
        out = total.sort_values(["Partes","Grupo","Alumno"], ascending=[False,True,True])

    out = out.reset_index(drop=True)
    out.insert(0, "Rank", out.index + 1)
    return out

def ranking_profesores(start: date, end: date, estado: str = "Todos",
                       grupo: str = "Todos", alumno: str = "Todos") -> pd.DataFrame:
    where = ["fecha BETWEEN ? AND ?"]
    params = [start.isoformat(), end.isoformat()]
    if estado in ("pendiente", "cerrado"):
        where.append("estado = ?"); params.append(estado)
    if grupo and grupo != "Todos":
        where.append("grupo = ?"); params.append(grupo)
    if alumno and alumno != "Todos":
        where.append("alumno = ?"); params.append(alumno)
    sql = f"""
        SELECT teacher_name AS Profesor, COUNT(*) AS Partes
        FROM incidents
        WHERE {' AND '.join(where)}
        GROUP BY teacher_name
        ORDER BY Partes DESC, teacher_name ASC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    df = pd.DataFrame(rows, columns=["Profesor","Partes"])
    if df.empty:
        return df
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df

# =========================
# UTILIDADES: PDF y EXCEL
# =========================
def df_to_pdf_bytes(df: pd.DataFrame, title: str = "Informe") -> bytes:
    if not HAS_REPORTLAB or df is None or df.empty:
        return b""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()
    style_cell = styles["BodyText"]
    style_cell.fontSize = 9
    style_cell.leading = 11

    elems = [Paragraph(title, styles["Heading2"]), Spacer(1, 8)]

    data = [[Paragraph(str(col), styles["Heading4"]) for col in df.columns]]
    for _, row in df.astype(str).iterrows():
        data.append([Paragraph(val, style_cell) for val in row.tolist()])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightcyan]),
    ]))
    doc.build(elems + [table])
    return buf.getvalue()

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Datos") -> bytes:
    """Exporta un DataFrame a Excel (.xlsx) y devuelve los bytes."""
    if df is None or df.empty:
        df = pd.DataFrame()
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()

# ===== PDF: ticket del parte (impresión inmediata tras enviar) =====
def incident_ticket_pdf(
    alumno: str,
    fecha: date,
    hora: str,
    profesor: str,
    descripcion: str,
    gravedad_inicial: str,
    enviado_por: str,
    enviado_dt: datetime | None = None,
) -> bytes:
    """
    Genera un PDF de 'ticket' con:
      - Título: "Parte de Incidencias. IES Antonio García Bellido."
      - 1ª línea: Alumno, Fecha, Hora
      - 2ª línea: Profesor
      - 3ª línea y siguientes: Descripción (multilínea)
      - Debajo: Catalogación de gravedad inicial
      - Pie: *** Enviado a Jefatura el (Fecha) a las (Hora) por (Usuario) ***
    """
    if not HAS_REPORTLAB:
        return b""

    if enviado_dt is None:
        enviado_dt = datetime.now()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,  # vertical
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    st_title = styles["Title"]
    st_body = styles["BodyText"]; st_body.fontSize = 11; st_body.leading = 14

    elems = []
    # Título
    elems.append(Paragraph("Parte de Incidencias. IES Antonio García Bellido.", st_title))
    elems.append(Spacer(1, 12))

    # Líneas superiores
    f_str = fecha.strftime("%d/%m/%Y") if isinstance(fecha, (date, datetime)) else str(fecha)
    elems.append(Paragraph(f"<b>Alumno:</b> {alumno} &nbsp;&nbsp; <b>Fecha:</b> {f_str} &nbsp;&nbsp; <b>Hora:</b> {hora}", st_body))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(f"<b>Profesor:</b> {profesor}", st_body))
    elems.append(Spacer(1, 10))

    # Descripción multilínea
    desc_html = (descripcion or "").replace("\n", "<br/>")
    elems.append(Paragraph(f"<b>Descripción:</b><br/>{desc_html}", st_body))
    elems.append(Spacer(1, 10))

    # Gravedad
    elems.append(Paragraph(f"<b>Gravedad (inicial):</b> {gravedad_inicial}", st_body))
    elems.append(Spacer(1, 18))

    # Pie
    elems.append(Paragraph(
        f"<i>*** Enviado a Jefatura el {enviado_dt.strftime('%d/%m/%Y')} "
        f"a las {enviado_dt.strftime('%H:%M')} por {enviado_por} ***</i>",
        st_body
    ))

    doc.build(elems)
    return buf.getvalue()

# =========================
# NUEVOS PDFs (reemplazo total)
# =========================

def _normalize_fecha_hora_for_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas 'Fecha' (a datetime) y 'Hora' (usa 'Franja' si no existe)."""
    dfn = df.copy()
    # Normalizar Fecha
    dfn["_Fecha_dt"] = pd.to_datetime(dfn["Fecha"], errors="coerce")
    # Normalizar Hora
    if "Hora" not in dfn.columns and "Franja" in dfn.columns:
        dfn["Hora"] = dfn["Franja"]
    dfn["Hora"] = dfn["Hora"].astype(str)
    # Índice de franja
    franja_order = {f: i for i, f in enumerate(FRANJAS)}
    dfn["_Hora_idx"] = dfn["Hora"].map(franja_order).fillna(99).astype(int)
    return dfn

def teacher_report_pdf(dfc: pd.DataFrame, profesor: str) -> bytes:
    """
    PDF del profesor (7 columnas; mismo formato reducido que el de alumnos):
    1 Nº correlativo
    2 Fecha
    3 Hora
    4 Alumno (ancha)
    5 Grupo
    6 Descripción (muy ancha)
    7 (Columna vacía para equilibrar / o se reparte en Descripción)  -> En esta versión NO usamos columna extra,
       y todo el espacio de 'Profesor' se reparte en Alumno + Descripción.

    SIN columnas de gravedad.
    SIN columna 'Profesor' (redundante, el informe ya es del profesor X).
    Orden impresión: más reciente → más antiguo.
    Anchos fijos (A4 horizontal, 794 pt útiles).
    """
    if not HAS_REPORTLAB or dfc is None or dfc.empty or not profesor:
        return b""

    df = dfc.copy()
    # Por seguridad, si llega 'Profesor' en el DF, filtramos
    if "Profesor" in df.columns:
        df = df[df["Profesor"].astype(str) == str(profesor)]
    if df.empty:
        return b""

    # Normalizar Fecha y Hora
    df["_Fecha_dt"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if "Hora" not in df.columns and "Franja" in df.columns:
        df["Hora"] = df["Franja"].astype(str)
    elif "Hora" not in df.columns:
        df["Hora"] = ""

    franja_order = {f: i for i, f in enumerate(FRANJAS)}
    df["_Hora_idx"] = df["Hora"].map(franja_order).fillna(99).astype(int)

    for c in ["Alumno", "Grupo", "Descripción"]:
        if c not in df.columns:
            df[c] = ""

    # Correlativo 1 = más antiguo
    df_hist = df.sort_values(
        ["_Fecha_dt", "_Hora_idx", "ID"],
        ascending=[True, True, True],
        na_position="last"
    ).copy()
    df_hist["#"] = range(1, len(df_hist) + 1)

    # Impresión: más reciente → más antiguo
    df_print = df_hist.sort_values(
        ["_Fecha_dt", "_Hora_idx", "ID"],
        ascending=[False, False, False]
    ).copy()

    df_print["Fecha"] = df_print["_Fecha_dt"].dt.strftime("%d/%m/%Y").fillna(df_print["Fecha"].astype(str))
    for c in ["Alumno", "Grupo", "Descripción", "Hora"]:
        df_print[c] = df_print[c].astype(str)

    # Estructura 7 columnas -> aquí SIN 'Profesor'
    df_out = df_print[["#", "Fecha", "Hora", "Alumno", "Grupo", "Descripción"]].copy()

    # --------------- PDF ---------------
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()
    style_title = styles["Heading2"]
    style_cell = styles["BodyText"]; style_cell.fontSize = 9; style_cell.leading = 11

    elems = []
    hoy = datetime.now().strftime("%d/%m/%Y")
    titulo = f"Historial del profesor {profesor} — {hoy}"
    elems.append(Paragraph(titulo, style_title))
    elems.append(Spacer(1, 10))

    # 🔒 ANCHOS FIJOS (repartiendo el hueco de 'Profesor' en Alumno + Descripción)
    # Para mantener la familia de anchos, tomamos la base del informe de alumnos:
    #   [40, 70, 60, 150, 150, 70, 254]
    # y como no hay 'Profesor', traspasamos esos 150 pt al par (Alumno + Descripción).
    # Propuesta equilibrada:
    col_widths = [
        40,   # #
        70,   # Fecha
        60,   # Hora
        210,  # Alumno (ancha, +60 sobre los 150 base)
        70,   # Grupo
        344   # Descripción (muy ancha, +150-60=+90 sobre los 254 base)
    ]
    # Suma: 40 + 70 + 60 + 210 + 70 + 344 = 794

    # Construimos cabeceras considerando 6 visibles (hemos eliminado la 7ª etiqueta)
    headers = ["#", "Fecha", "Hora", "Alumno", "Grupo", "Descripción"]
    data = [[Paragraph(h, styles["Heading4"]) for h in headers]]

    for _, r in df_out.iterrows():
        data.append([
            Paragraph(str(r["#"]), style_cell),
            Paragraph(str(r["Fecha"]), style_cell),
            Paragraph(str(r["Hora"]), style_cell),
            Paragraph(str(r["Alumno"]), style_cell),
            Paragraph(str(r["Grupo"]), style_cell),
            Paragraph(str(r["Descripción"]), style_cell),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightcyan]),
    ]))

    elems.append(table)
    doc.build(elems)
    return buf.getvalue()

def student_report_pdf(dfc: pd.DataFrame, alumno: str | None = None, grupo: str | None = None) -> bytes:
    """
    PDF historial de alumnos (7 columnas):
    1 Nº correlativo
    2 Fecha
    3 Hora
    4 Profesor (ancha)
    5 Alumno (ancha)
    6 Grupo
    7 Descripción (muy ancha)

    SIN columnas de gravedad.
    Orden impresión: más reciente → más antiguo.
    Anchos fijos de columna (A4 horizontal, 794 pt útiles).
    """

    if not HAS_REPORTLAB or dfc is None or dfc.empty:
        return b""

    df = dfc.copy()

    # Filtrar por alumno/grupo si se proporcionan
    if alumno:
        df = df[df["Alumno"].astype(str) == str(alumno)]
    if grupo and grupo != "Todos":
        df = df[df["Grupo"].astype(str) == str(grupo)]
    if df.empty:
        return b""

    # Normalización interna
    df["_Fecha_dt"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Normalizar hora (“Hora” o “Franja” según venga)
    if "Hora" not in df.columns and "Franja" in df.columns:
        df["Hora"] = df["Franja"].astype(str)
    elif "Hora" not in df.columns:
        df["Hora"] = ""

    franja_order = {f: i for i, f in enumerate(FRANJAS)}
    df["_Hora_idx"] = df["Hora"].map(franja_order).fillna(99).astype(int)

    # Asegurar columnas necesarias
    for c in ["Profesor", "Alumno", "Grupo", "Descripción"]:
        if c not in df.columns:
            df[c] = ""

    # Correlativo ascendente (1= más antiguo)
    df_hist = df.sort_values(
        ["_Fecha_dt", "_Hora_idx", "ID"],
        ascending=[True, True, True],
        na_position="last"
    ).copy()
    df_hist["#"] = range(1, len(df_hist) + 1)

    # Orden de impresión: más reciente → más antiguo
    df_print = df_hist.sort_values(
        ["_Fecha_dt", "_Hora_idx", "ID"],
        ascending=[False, False, False]
    ).copy()

    # Formatos finales
    df_print["Fecha"] = df_print["_Fecha_dt"].dt.strftime("%d/%m/%Y").fillna(df_print["Fecha"].astype(str))
    for c in ["Profesor", "Alumno", "Grupo", "Descripción", "Hora"]:
        df_print[c] = df_print[c].astype(str)

    # Selección final SIN las columnas de gravedad
    df_out = df_print[["#", "Fecha", "Hora", "Profesor", "Alumno", "Grupo", "Descripción"]]

    # ---------------- PDF ----------------
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()
    style_title = styles["Heading2"]
    style_cell = styles["BodyText"]
    style_cell.fontSize = 9
    style_cell.leading = 11

    elems = []
    hoy = datetime.now().strftime("%d/%m/%Y")
    titulo = "Historial de alumnos"
    if alumno: titulo += f" — {alumno}"
    if grupo and grupo != "Todos": titulo += f" ({grupo})"
    titulo += f" — {hoy}"

    elems.append(Paragraph(titulo, style_title))
    elems.append(Spacer(1, 10))

    # ---------------- ANCHOS FIJOS ----------------
    # Total útil en A4 apaisado: 794 pt
    col_widths = [
        40,   # #
        70,   # Fecha
        60,   # Hora
        150,  # Profesor (ancha)
        150,  # Alumno (ancha)
        70,   # Grupo
        254   # Descripción (muy ancha)
    ]
    # Suma = 40 + 70 + 60 + 150 + 150 + 70 + 254 = 794 pt EXACTOS

    # Construcción tabla
    headers = list(df_out.columns)
    data = [[Paragraph(h, styles["Heading4"]) for h in headers]]

    for _, r in df_out.iterrows():
        data.append([
            Paragraph(str(r["#"]), style_cell),
            Paragraph(str(r["Fecha"]), style_cell),
            Paragraph(str(r["Hora"]), style_cell),
            Paragraph(str(r["Profesor"]), style_cell),
            Paragraph(str(r["Alumno"]), style_cell),
            Paragraph(str(r["Grupo"]), style_cell),
            Paragraph(str(r["Descripción"]), style_cell),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ALIGN",      (0,0), (-1,-1), "LEFT"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightcyan]),
    ]))

    elems.append(table)
    doc.build(elems)

    return buf.getvalue()
# =========================
# UI helper: gravedad con 3 checkboxes exclusivos (validación en submit)
# =========================
def gravedad_selector(key_prefix: str, default: str | None = None, show_helper_msg: bool = True) -> str | None:
    keys = {
        "leve": f"{key_prefix}_leve",
        "grave": f"{key_prefix}_grave",
        "muy_grave": f"{key_prefix}_muygrave",
    }
    if not any(k in st.session_state for k in keys.values()):
        st.session_state[keys["leve"]] = False
        st.session_state[keys["grave"]] = False
        st.session_state[keys["muy_grave"]] = False

    c1, c2, c3 = st.columns(3)
    v_leve = c1.checkbox("Leve", key=keys["leve"])
    v_grave = c2.checkbox("Grave", key=keys["grave"])
    v_muy = c3.checkbox("Muy grave", key=keys["muy_grave"])

    seleccionadas = []
    if v_leve: seleccionadas.append("leve")
    if v_grave: seleccionadas.append("grave")
    if v_muy: seleccionadas.append("muy grave")

    if len(seleccionadas) == 1:
        return seleccionadas[0]

    if show_helper_msg:
        if len(seleccionadas) == 0:
            st.info("Marca una gravedad (elige una).")
        else:
            st.warning("Has marcado más de una gravedad. Deja solo una marcada.")
    return None

# ===== Helper para resetear formularios “Nuevo parte” =====
def reset_nuevo_parte_form(prefix: str):
    keys_to_clear = [
        f"{prefix}grupo", f"{prefix}alumno",
        f"{prefix}grupo_prev",
        f"{prefix}fecha", f"{prefix}franja",
        f"{prefix}desc",
        # Variantes del rol profesor
        f"{prefix}grupo_prof", f"{prefix}alumno_prof",
        f"{prefix}grupo_prev_prof", f"{prefix}fecha_prof",
        f"{prefix}franja_prof", f"{prefix}desc_prof",
        # Variantes de director/convivencia
        f"{prefix}grupo_dir", f"{prefix}alumno_dir",
        f"{prefix}fecha_dir", f"{prefix}franja_dir", f"{prefix}desc_dir",
        f"{prefix}grupo_conv", f"{prefix}alumno_conv",
        f"{prefix}fecha_conv", f"{prefix}franja_conv", f"{prefix}desc_conv",
    ]
    grav_keys = [
        f"{prefix}grav_ini_leve", f"{prefix}grav_ini_grave", f"{prefix}grav_ini_muygrave",
        f"{prefix}grav_ini_prof_leve", f"{prefix}grav_ini_prof_grave", f"{prefix}grav_ini_prof_muygrave",
        f"{prefix}grav_ini_dir_leve", f"{prefix}grav_ini_dir_grave", f"{prefix}grav_ini_dir_muygrave",
        f"{prefix}grav_ini_conv_leve", f"{prefix}grav_ini_conv_grave", f"{prefix}grav_ini_conv_muygrave",
    ]
    for k in keys_to_clear + grav_keys:
        if k in st.session_state:
            st.session_state.pop(k, None)

# ===== Home / pantalla general tras enviar un parte =====
def show_home_header():
    if Path(HERE/"logo.png").exists():
        st.image(str(HERE/"logo.png"), width=180)
    st.title("📋 Partes de Incidencias de Alumnado")

# === Estilo de la pantalla de login: fondo degradado + card central ===
def apply_login_theme(gradient: str = None):
    if gradient is None:
        gradient = "linear-gradient(135deg, #cfe9d9 0%, #a3d9b1 50%, #7ac69a 100%)"

    custom_css = f"""
    <style>
    .stApp {{
        background: {gradient};
        background-attachment: fixed;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(3px);
    }}

    .login-card {{
        max-width: 540px;
        margin: 4rem auto 2rem auto;
        padding: 2rem 1.5rem;
        background: rgba(255, 255, 255, 0.92);
        border-radius: 16px;
        box-shadow: 0 12px 28px rgba(30, 41, 59, 0.18), 0 8px 10px rgba(30, 41, 59, 0.10);
        border: 1px solid rgba(148,163,184,0.25);
    }}

    .login-card h1, .login-card h2, .login-card h3 {{
        text-align: center;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
    }}

    .stButton > button {{
        border-radius: 12px !important;
        padding: 0.6rem 0.9rem !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 16px rgba(30, 41, 59, 0.12);
    }}

    /* ==== INPUTS DESTACADOS EN LOGIN ==== */
    /* Contenedores de Email/Password dentro de la card */
    .login-card .stTextInput, .login-card .stPassword {{
        margin-bottom: 0.8rem;
    }}

    /* Caja del input (envoltorio) */
    .login-card .stTextInput > div > div,
    .login-card .stPassword   > div > div {{
        background: #ffffff;                     /* Fondo blanco nítido */
        border: 1px solid rgba(148,163,184,0.45);/* Gris suave */
        border-radius: 12px;                     /* Bordes redondeados */
        box-shadow: 0 3px 10px rgba(30,41,59,0.06);
        transition: box-shadow .2s ease, border-color .2s ease;
    }}

    /* El propio input */
    .login-card .stTextInput input,
    .login-card .stPassword   input {{
        background: transparent;                 /* Fondo ya lo pone el wrapper */
        border: none;
        outline: none;
        border-radius: 12px;                     /* Redondeo coherente */
        padding: 0.55rem 0.75rem;                /* Respiración */
        font-size: 0.98rem;
        color: #111827;                          /* Texto oscuro */
    }}

    /* Placeholder más visible sobre el degradado */
    .login-card input::placeholder {{
        color: #6b7280;                          /* Gris medio */
        opacity: 1;
    }}

    /* Estado foco/hover: resaltado visible y accesible */
    .login-card .stTextInput > div > div:focus-within,
    .login-card .stPassword   > div > div:focus-within {{
        border-color: #5B6CFF;                   /* Primario */
        box-shadow: 0 0 0 3px rgba(91,108,255,0.20);
    }}
    .login-card .stTextInput > div > div:hover,
    .login-card .stPassword   > div > div:hover {{
        border-color: #64748b;                   /* Gris un pelín más intenso */
    }}

    /* Centrado del logo (si decides ponerlo dentro del card) */
    .login-logo {{
        display: block;
        margin: 0 auto 0.5rem auto;
    }}
    </style>
    """
    import streamlit as st
    st.markdown(custom_css, unsafe_allow_html=True)


# Context manager para crear la "card" del login
from contextlib import contextmanager

@contextmanager
def login_card():
    """
    Abre un contenedor con clase 'login-card' para centrar y estilizar el área de login.
    Uso:  with login_card(): ...
    """
    import streamlit as st
    _container = st.container()
    with _container:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        try:
            yield
        finally:
            st.markdown('</div>', unsafe_allow_html=True)
def go_home_after_submit(message: str | None):
    """Envía al usuario a la pantalla general tras enviar un parte."""
    st.session_state["show_menu"] = False
    if message:
        st.session_state["last_success_message"] = message

# ===== Helper: inicio del curso escolar =====
def school_year_start(today: date | None = None) -> date:
    """
    Devuelve el 1 de septiembre del curso vigente:
      - Si hoy es septiembre (mes >= 9) o posterior: 1/9 del año actual.
      - Si hoy es antes de septiembre: 1/9 del año anterior.
    Esto permite que la fecha por defecto de filtros sea coherente con el curso escolar.
    """
    if today is None:
        today = date.today()
    year = today.year if today.month >= 9 else today.year - 1
    return date(year, 9, 1)

# ========== BLOQUE 4/7: PDFs Alumno y Profesor (ya redefinidos arriba) ==========

# (Las nuevas funciones teacher_report_pdf y student_report_pdf han reemplazado a las antiguas)

# ========== BLOQUE 5/7: Login, Primer Acceso ==========

def bootstrap_admin_screen():
    st.title("🛠 Configuración inicial")
    st.write("Crea el **primer usuario** (Jefe de estudios).")

    name = st.text_input("Nombre completo", key="boot_name")
    email = st.text_input("Email", key="boot_email")
    p1 = st.text_input("Contraseña", type="password", key="boot_p1")
    p2 = st.text_input("Repetir contraseña", type="password", key="boot_p2")

    if st.button("Crear Jefe de estudios", key="boot_create", use_container_width=True):
        if not name or not email:
            st.error("Nombre y email obligatorios."); return
        if p1 != p2:
            st.error("Las contraseñas no coinciden."); return
        if len(p1) < 4:
            st.error("Contraseña demasiado corta."); return

        ok, msg = create_user(name, email, "jefe")
        if ok:
            uid = get_user_by_email(email)[0]
            set_user_password(uid, p1)
            st.success("Jefe creado. Inicia sesión.")
            st.session_state.clear(); st.rerun()
        else:
            st.error(msg)

def login_screen():
    import streamlit as st
    from pathlib import Path

    # 🎨 fondo degradado
    apply_login_theme()

    # Logo centrado (si existe)
    if Path(HERE/"logo.png").exists():
        st.image(str(HERE/"logo.png"), width=160)

    # 🃏 card centrado
    with login_card():
        st.title(APP_TITLE)
        st.subheader("🔐 Acceso")

        email = st.text_input("Email", key="login_email")
        if st.button("Continuar", key="login_continue", use_container_width=True):
            u = get_user_by_email(email)
            if not u:
                st.error("Email no registrado."); return
            uid, name, email, role, pw_hash, active = u
            if active == 0:
                st.error("Tu cuenta está suspendida. Contacta con Jefatura."); return
            if pw_hash is None:
                st.session_state["pending_user"] = {"id": uid, "name": name, "email": email, "role": role}
                st.session_state["needs_password_setup"] = True; st.rerun()
            else:
                st.session_state["login_user"] = u
                st.session_state["ask_password"] = True; st.rerun()

def first_password_screen():
    import streamlit as st
    from pathlib import Path

    apply_login_theme()

    if Path(HERE/"logo.png").exists():
        st.image(str(HERE/"logo.png"), width=160)

    with login_card():
        st.title(APP_TITLE)
        st.subheader("🔑 Crear contraseña (primer acceso)")

        p1 = st.text_input("Nueva contraseña", type="password", key="first_p1")
        p2 = st.text_input("Repetir contraseña", type="password", key="first_p2")
        if st.button("Guardar", key="first_save", use_container_width=True):
            if p1 != p2:
                st.error("Las contraseñas no coinciden."); return
            if len(p1) < 4:
                st.error("Debe tener al menos 4 caracteres."); return
            u = st.session_state.get("pending_user")
            if not u:
                st.error("Sesión expirada. Vuelve a iniciar sesión."); return
            set_user_password(u["id"], p1)
            st.success("Contraseña creada. Inicia sesión.")
            st.session_state.clear(); st.rerun()

def password_login_screen():
    import streamlit as st
    from pathlib import Path

    apply_login_theme()

    if Path(HERE/"logo.png").exists():
        st.image(str(HERE/"logo.png"), width=160)

    with login_card():
        st.title(APP_TITLE)
        st.subheader("🔒 Contraseña")
        u = st.session_state["login_user"]
        uid, name, email, role, pw_hash, active = u
        p = st.text_input("Contraseña", type="password", key="pass_login")
        if st.button("Entrar", key="pass_enter", use_container_width=True):
            if active == 0:
                st.error("Cuenta suspendida. Contacta con Jefatura."); return
            if verify_password(p, pw_hash):
                st.session_state["user"] = {"id": uid, "name": name, "email": email, "role": role}
                st.session_state.pop("login_user", None); st.session_state.pop("ask_password", None)
                st.session_state["show_menu"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")

def excursion_banlist_multi(activity_date: date, grupos_filtro: list[str] | None = None, lookback_days: int = 30) -> pd.DataFrame:
    """
    Versión multi-grupo: devuelve alumnos NO aptos (partes CERRADOS con gravedad GRAVE o MUY GRAVE
    en los últimos lookback_days días hasta activity_date), filtrando por una lista de grupos.
    Si grupos_filtro es None o [], se consideran TODOS los grupos.
    """
    start = activity_date - timedelta(days=lookback_days)
    graves = ("grave","muy grave")

    # Filtro de 30 días (cerrados + gravedad final grave/muy grave + fecha en ventana)
    where_30 = ["estado='cerrado'", "fecha BETWEEN ? AND ?", f"gravedad_final IN ({','.join('?'*len(graves))})"]
    params_30 = [start.isoformat(), activity_date.isoformat(), *graves]

    # Filtro por varios grupos (IN) si procede
    if grupos_filtro and len(grupos_filtro) > 0:
        placeholders = ",".join("?" for _ in grupos_filtro)
        where_30.append(f"grupo IN ({placeholders})")
        params_30.extend(grupos_filtro)

    sql_30 = f"""
        SELECT grupo, alumno, COUNT(*) as cnt
        FROM incidents
        WHERE {' AND '.join(where_30)}
        GROUP BY grupo, alumno
    """

    # Totales por alumno (para columna Partes_totales)
    where_tot = []
    params_tot = []
    if grupos_filtro and len(grupos_filtro) > 0:
        placeholders = ",".join("?" for _ in grupos_filtro)
        where_tot.append(f"grupo IN ({placeholders})")
        params_tot.extend(grupos_filtro)

    sql_tot = "SELECT grupo, alumno, COUNT(*) as cnt FROM incidents"
    if where_tot:
        sql_tot += " WHERE " + " AND ".join(where_tot)
    sql_tot += " GROUP BY grupo, alumno"

    with get_conn() as conn:
        rows_30d = conn.execute(sql_30, tuple(params_30)).fetchall()
        rows_tot = conn.execute(sql_tot, tuple(params_tot)).fetchall()

    df_30 = pd.DataFrame(rows_30d, columns=["Grupo","Alumno","Partes_30d"])
    df_tot = pd.DataFrame(rows_tot, columns=["Grupo","Alumno","Partes_totales"])

    if df_30.empty:
        return pd.DataFrame(columns=["Grupo","Alumno","Partes_30d","Partes_totales"])

    df = df_30.merge(df_tot, on=["Grupo","Alumno"], how="left").fillna({"Partes_totales": 0})
    df["Partes_30d"] = df["Partes_30d"].astype(int)
    df["Partes_totales"] = df["Partes_totales"].astype(int)
    return df.sort_values(["Grupo","Alumno"]).reset_index(drop=True)

# ========== BLOQUE 6/7: App principal (Tabs por rol) ==========

def main():
    st.set_page_config(
        page_title="Partes de Incidencias",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    init_db()

    # Cargar alumnos.xlsx si existe (una vez por sesión)
    if "alumnos_loaded" not in st.session_state:
        try:
            load_alumnos_from_excel_if_exists()
        except Exception as ex:
            st.sidebar.warning(f"No se pudo importar alumnos.xlsx: {ex}")
        st.session_state["alumnos_loaded"] = True

    # Bootstrap si no hay usuarios
    if no_users_exist():
        bootstrap_admin_screen(); return

    # Flujo login / primer acceso
    if "needs_password_setup" in st.session_state:
        first_password_screen(); return
    if "ask_password" in st.session_state:
        password_login_screen(); return
    if "user" not in st.session_state:
        login_screen(); return

    usuario = st.session_state["user"]

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        if Path(HERE / "logo.png").exists():
            st.image(str(HERE / "logo.png"), width=150)
        st.markdown("---")
        rol_map = {"jefe": "Jefatura", "profesor": "Profesor", "director": "Director", "convivencia": "Convivencia"}
        st.write(f"👤 **{usuario['name']}** ({rol_map.get(usuario['role'], usuario['role'])})")

        if st.button("Cerrar sesión", key="side_logout", use_container_width=True):
            st.session_state.clear(); st.rerun()

        st.markdown("---")
        st.subheader("🔑 Cambiar contraseña")
        old = st.text_input("Contraseña actual", type="password", key="side_old")
        new1 = st.text_input("Nueva", type="password", key="side_new1")
        new2 = st.text_input("Repetir", type="password", key="side_new2")
        if st.button("Actualizar contraseña", key="side_update_pwd", use_container_width=True):
            u = get_user_by_email(usuario["email"])
            if not u or not u[4]:
                st.error("No se encontró tu usuario o no tiene contraseña definida.")
            elif not verify_password(old, u[4]):
                st.error("La contraseña actual no es correcta.")
            elif new1 != new2:
                st.error("Las nuevas contraseñas no coinciden.")
            elif len(new1) < 4:
                st.error("La nueva contraseña es demasiado corta.")
            else:
                set_user_password(usuario["id"], new1)
                st.success("Contraseña actualizada.")

        st.markdown("---")
        if usuario["role"] == "jefe":
            # ===== Importar alumnos =====
            st.subheader("📥 Importar alumnos (Excel)")
            st.caption("Debe tener columnas: **Grupo** y **Alumno**")
            up_alum = st.file_uploader("Selecciona Excel de alumnos", type=["xlsx"], key="side_up_alum")
            mode_merge = st.checkbox("Fusionar (no borrar existentes)", value=True, key="side_al_merge")

            if st.button("Actualizar alumnos", key="side_btn_alum", use_container_width=True):
                if up_alum is None:
                    st.error("Selecciona un archivo Excel.")
                else:
                    try:
                        df_up = pd.read_excel(up_alum, engine="openpyxl")
                        import_alumnos_df_to_db(df_up, mode="merge" if mode_merge else "replace")
                        st.success("Alumnos actualizados.")
                    except Exception as ex:
                        st.error(f"No se pudo importar: {ex}")

            st.markdown("---")
            # ===== Añadir alumno a mano =====
            st.subheader("➕ Añadir alumno a mano")
            grupos_existentes = list_grupos()
            colg, cola = st.columns([1,2])
            with colg:
                g_manual = st.text_input("Grupo", placeholder="Ej.: 2ºB", key="side_new_group")
                if not g_manual and grupos_existentes:
                    g_manual = st.selectbox("o elige grupo existente", [""] + grupos_existentes, key="side_new_group_sel")
            with cola:
                a_manual = st.text_input("Alumno", placeholder="Nombre y apellidos", key="side_new_student")

            if st.button("Añadir alumno", key="side_add_student", use_container_width=True):
                ok, msg = insert_student(g_manual, a_manual)
                (st.success if ok else st.error)(msg)

            st.markdown("---")
            # ===== Eliminar alumno a mano =====
            st.subheader("🗑️ Eliminar alumno a mano")

            # Selección de grupo y alumno (dependiente)
            grupos_existentes_del = list_grupos()
            colg_del, cola_del = st.columns([1, 2])

            with colg_del:
                g_del = st.selectbox("Grupo", options=grupos_existentes_del if grupos_existentes_del else ["(sin grupos)"], key="side_del_group")
            with cola_del:
                alumnos_del = list_alumnos_by_grupo(g_del) if grupos_existentes_del else []
                a_del = st.selectbox("Alumno", options=alumnos_del if alumnos_del else ["(sin alumnos)"], key="side_del_student")

            # Confirmación obligatoria
            confirm_del = st.checkbox("✅ ¿Estás seguro de que desea borrar este alumno?", key="side_del_confirm")

            # Acción: eliminar
            if st.button("Eliminar alumno", key="side_btn_del_student", use_container_width=True, disabled=not confirm_del):
                if not grupos_existentes_del or not alumnos_del or g_del in (None, "", "(sin grupos)") or a_del in (None, "", "(sin alumnos)"):
                    st.error("Selecciona un grupo y un alumno válidos.")
                elif not confirm_del:
                    st.warning("Debes confirmar el borrado marcando la casilla.")
                else:
                    ok, msg = delete_student(g_del, a_del)
                    (st.success if ok else st.error)(msg)
                    # Si se eliminó correctamente, refrescamos la lista para que desaparezca del selector
                    if ok:
                        st.rerun()
    
    # ======================================
    # Pantalla general tras crear un parte
    # ======================================
    if st.session_state.get("show_menu", True) is False:
        show_home_header()
        last_msg = st.session_state.pop("last_success_message", None)
        if last_msg:
            st.success(last_msg)
        st.info("Si quieres registrar otro parte, pulsa el botón de abajo y vuelve a seleccionar **«Nuevo parte»** en el menú.")
        if st.button("Ir al menú", use_container_width=True):
            st.session_state["show_menu"] = True
            st.rerun()
        return

    # ---------------- TABS por ROL ----------------
    show_home_header()
    rol = usuario["role"]

    # =============== JEFATURA ===============
    if rol == "jefe":
        try:
            pend_count = len(list_pending_incidents())
        except Exception:
            pend_count = 0

        tabs = st.tabs([
            "📝 Nuevo parte",
            "🚫 Excursiones",
            "🔥 Ranking de alumnos",
            "📚 Historial de alumnos",
            "👨‍🏫 Historial de profesores",
            f"📬 Pendientes · {pend_count}",
            "📊 Estadísticas",
            "📈 Gráficos",
            "👥 Usuarios"
        ])

        # ----- TAB 0: Nuevo parte (Jefatura) -----
        with tabs[0]:
            st.subheader("📝 Nuevo parte")
            grupos = list_grupos()
            if not grupos:
                st.warning("No hay grupos cargados. La Jefatura debe importar 'alumnos.xlsx'.")
            else:
                col_g, col_a = st.columns([1, 2])
                grupo_sel = col_g.selectbox("Grupo", options=grupos, key="p_grupo")
                if "p_grupo_prev" not in st.session_state or st.session_state["p_grupo_prev"] != grupo_sel:
                    st.session_state["p_alumno"] = None
                    st.session_state["p_grupo_prev"] = grupo_sel

                alumnos = list_alumnos_by_grupo(grupo_sel)
                if not alumnos:
                    col_a.error("Este grupo no tiene alumnos cargados.")
                    alumno_sel = None
                else:
                    prev_al = st.session_state.get("p_alumno")
                    idx = alumnos.index(prev_al) if prev_al in alumnos else 0
                    alumno_sel = col_a.selectbox("Alumno", options=alumnos, key="p_alumno", index=idx)

                with st.form("p_form_parte"):
                    col1, col2 = st.columns(2)
                    with col1:
                        # 🚫 Bloquear fechas futuras en UI
                        fecha_sel = st.date_input("Fecha", value=date.today(), max_value=date.today(), key="p_fecha")
                    with col2:
                        franja_sel = st.selectbox("Franja horaria", FRANJAS, key="p_franja")
                    st.markdown("**Gravedad (inicial)**")
                    grav_ini = gravedad_selector("p_grav_ini", default=None)
                    descripcion = st.text_area("Descripción (obligatoria)", key="p_desc")
                    enviar = st.form_submit_button("Enviar parte a Jefatura", use_container_width=True)

                if enviar:
                    if not alumnos or not alumno_sel or not grupo_sel:
                        st.error("Grupo y alumno son obligatorios.")
                    elif not descripcion or not descripcion.strip():
                        st.error("La descripción es obligatoria.")
                    elif grav_ini not in ("leve","grave","muy grave"):
                        st.error("Debes seleccionar exactamente una gravedad (marca un único tick).")
                    else:
                        ok, msg = create_incident(
                            teacher_id=usuario["id"], teacher_name=usuario["name"],
                            grupo=grupo_sel, alumno=alumno_sel,
                            fecha=fecha_sel, franja=franja_sel,
                            descripcion=descripcion.strip(), gravedad_inicial=grav_ini
                        )
                        if ok:
                            reset_nuevo_parte_form("p_")
                            go_home_after_submit(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        # ----- TAB 1: No aptos (Jefatura) -----
        with tabs[1]:
            st.subheader("🚫 Alumnos no aptos para excursión")
            st.caption("NO aptos: partes **cerrados** con gravedad **grave o muy grave** en los **X días previos** a la fecha elegida.")
        
            # === Controles ===
            colx, coly, colz = st.columns([1.2, 2.2, 1.0])
            with colx:
                fecha_actividad = st.date_input("Fecha de la actividad", value=date.today(), key="exc_fecha")
        
            with coly:
                # 🔁 MULTISELECT de grupos (además de opción Todos simulada)
                grupos_all = list_grupos()
                grupos_sel = st.multiselect(
                    "Grupos (puedes elegir varios o dejar vacío para 'Todos')",
                    options=grupos_all,
                    default=[],
                    help="Si lo dejas vacío, se considerarán TODOS los grupos."
                )
        
                # Nombre de la actividad (para el título del PDF)
                actividad = st.text_input(
                    "Nombre de la actividad (para el PDF)",
                    placeholder="Ej.: Visita al Museo de Ciencias",
                    key="exc_actividad"
                )
        
            with colz:
                ventana = st.number_input(
                    "Ventana (días)",
                    min_value=7, max_value=90,
                    value=30, step=1, key="exc_dias"
                )
        
            # === Acción ===
            if st.button("Consultar", key="exc_consultar", use_container_width=True):
                # Llamamos a la versión multi-grupo (si lista vacía -> todos)
                df_ban = excursion_banlist_multi(
                    activity_date=fecha_actividad,
                    grupos_filtro=grupos_sel if len(grupos_sel) > 0 else None,
                    lookback_days=int(ventana)
                )
        
                if df_ban.empty:
                    st.success("No hay alumnos restringidos. ✅")
                else:
                    # Título informativo en la página
                    titulo = f"No aptos excursión — {fecha_actividad.strftime('%d/%m/%Y')}"
                    if grupos_sel and len(grupos_sel) > 0:
                        if len(grupos_sel) <= 3:
                            titulo += " — " + ", ".join(grupos_sel)
                        else:
                            titulo += f" — Varios grupos ({len(grupos_sel)})"
        
                    st.markdown(f"**{titulo}**")
                    st.dataframe(df_ban, use_container_width=True)
        
                    # === Exportación a PDF (con NOMBRE ACTIVIDAD EN TÍTULO) ===
                    if HAS_REPORTLAB:
                        # Armamos el título del PDF incluyendo el nombre de la actividad si se ha indicado
                        titulo_pdf = "No aptos excursión"
                        if actividad.strip():
                            titulo_pdf += f" — {actividad.strip()}"
                        titulo_pdf += f" — {fecha_actividad.strftime('%d/%m/%Y')}"
                        if grupos_sel and len(grupos_sel) > 0:
                            if len(grupos_sel) <= 3:
                                titulo_pdf += " — " + ", ".join(grupos_sel)
                            else:
                                titulo_pdf += f" — Varios grupos ({len(grupos_sel)})"
        
                        pdf_ban = df_to_pdf_bytes(df_ban, title=titulo_pdf)
        
                        # Nombre de archivo amigable
                        def _slug(s: str) -> str:
                            return "".join(ch for ch in s.replace(" ", "_") if ch.isalnum() or ch in ("_", "-")).strip("_")
        
                        nombre_act_slug = _slug(actividad) if actividad.strip() else "actividad"
                        grupos_slug = (
                            _slug("_".join(grupos_sel)) if (grupos_sel and len(grupos_sel) > 0)
                            else "todos"
                        )
                        fname_pdf = f"no_aptos_{nombre_act_slug}_{grupos_slug}_{fecha_actividad.isoformat()}.pdf"
        
                        st.download_button(
                            "📄 Exportar a PDF",
                            data=pdf_ban,
                            file_name=fname_pdf,
                            mime="application/pdf",
                            key="exc_pdf",
                            use_container_width=True
                        )
        
                    # === Exportación a Excel (sin necesidad del nombre de actividad) ===
                    xls = df_to_excel_bytes(df_ban, sheet_name="No_aptos")
                    fname_xlsx = f"no_aptos_{fecha_actividad.isoformat()}.xlsx"  # puedes incluir actividad si lo deseas
                    st.download_button(
                        "⬇️ Exportar a Excel (.xlsx)",
                        data=xls,
                        file_name=fname_xlsx,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="exc_xlsx",
                        use_container_width=True
                    )

        # ----- TAB 2: Disruptivos (Jefatura) -----
        with tabs[2]:
            st.subheader("🔥 Alumnos más disruptivos")
            col_a, col_b, col_c, col_d = st.columns([1,1,1,1.5])
            with col_a:
                f_ini_rk = st.date_input("Desde", value=school_year_start(), key="rk_ini")
            with col_b:
                f_fin_rk = st.date_input("Hasta", value=date.today(), key="rk_fin")
            with col_c:
                grupos_opt_rk = ["Todos"] + list_grupos()
                g_rk = st.selectbox("Grupo", grupos_opt_rk, key="rk_grupo")
            with col_d:
                solo_cerr = st.checkbox("Solo partes cerrados", value=True, key="rk_cerr")
                pond_grav = st.checkbox("Ponderar gravedad (L=1, G=2, MG=3)", value=True, key="rk_pond")
            df_rk = ranking_disruptivos(f_ini_rk, f_fin_rk, grupo_filtro=g_rk,
                                        solo_cerrados=solo_cerr, ponderar_gravedad=pond_grav)
            if df_rk.empty:
                st.info("No hay datos.")
            else:
                st.dataframe(df_rk, use_container_width=True)
                if HAS_REPORTLAB:
                    titulo = "Ranking alumnos más disruptivos"
                    if g_rk != "Todos": titulo += f" — {g_rk}"
                    titulo += f" ({f_ini_rk.strftime('%d/%m/%Y')} – {f_fin_rk.strftime('%d/%m/%Y')})"
                    pdf_rk = df_to_pdf_bytes(df_rk, title=titulo)
                    st.download_button("📄 Exportar a PDF", data=pdf_rk,
                        file_name=f"ranking_disruptivos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.pdf",
                        mime="application/pdf", key="rk_pdf", use_container_width=True)
                xls = df_to_excel_bytes(df_rk, sheet_name="Ranking")
                st.download_button("⬇️ Exportar a Excel (.xlsx)",
                    data=xls,
                    file_name=f"ranking_disruptivos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="rk_xlsx", use_container_width=True)

        # ----- TAB 3: Historial de alumnos (Jefatura) -----
        with tabs[3]:
            st.subheader("📚 Historial de alumnos (Jefatura)")
            c1, c2, c3 = st.columns([1,1,2])
            with c1: f_ini_a = st.date_input("Desde", value=school_year_start(), key="j_al_ini")
            with c2: f_fin_a = st.date_input("Hasta", value=date.today(), key="j_al_fin")
            with c3:
                g_al = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="j_al_grupo")
                a_opts = ["Todos"] + (list_alumnos_by_grupo(g_al) if g_al != "Todos" else [])
                a_sel = st.selectbox("Alumno", a_opts, key="j_al_alumno")
            df_al = filter_closed_incidents(f_ini_a, f_fin_a, g_al, a_sel)
            if df_al.empty:
                st.info("No hay partes cerrados con esos filtros.")
            else:
                st.dataframe(df_al, use_container_width=True)

                # PDF con nuevo formato (7 columnas) sobre la tabla filtrada
                if HAS_REPORTLAB:
                    # Si quieres que respete alumno/grupo seleccionados:
                    pdf_custom = student_report_pdf(df_al, alumno=(a_sel if a_sel and a_sel != "Todos" else None),
                                    grupo=(g_al if g_al and g_al != "Todos" else None))
                    st.download_button(
                        "📄 Exportar historial (PDF, 7 columnas)",
                        data=pdf_custom,
                        file_name=f"historial_alumnos_custom_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.pdf",
                        mime="application/pdf",
                        key="hist_alumnos_pdf_custom",
                        use_container_width=True
                    )
                
                if HAS_REPORTLAB and g_al != "Todos" and a_sel != "Todos":
                    pdf_al = student_report_pdf(df_al, alumno=a_sel, grupo=g_al)
                    st.download_button("📄 Informe del alumno (PDF)", data=pdf_al,
                        file_name=f"informe_{a_sel.replace(' ','_')}_{date.today().isoformat()}.pdf",
                        mime="application/pdf", key="j_al_pdf", use_container_width=True)
                xls = df_to_excel_bytes(df_al, sheet_name="Historial_alumnos")
                st.download_button("⬇️ Exportar a Excel (.xlsx)",
                    data=xls,
                    file_name=f"historial_alumnos_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="j_al_xlsx", use_container_width=True)

        # ----- TAB 4: Historial de profesores (Jefatura) -----
        with tabs[4]:
            st.subheader("👨‍🏫 Historial de profesores (Jefatura)")
            c1, c2, c3 = st.columns([1,1,2])
            with c1: f_ini_p = st.date_input("Desde", value=school_year_start(), key="j_pr_ini")
            with c2: f_fin_p = st.date_input("Hasta", value=date.today(), key="j_pr_fin")
            with c3: estado_p = st.selectbox("Estado", ["Todos","pendiente","cerrado"], key="j_pr_estado")
            prof_opts = ["Todos"] + list_profesor_names()
            prof = st.selectbox("Profesor", prof_opts, index=0, key="j_pr_prof")
            g_pr = st.selectbox("Grupo (opcional)", ["Todos"] + list_grupos(), key="j_pr_grupo")
            a_pr = st.selectbox("Alumno (opcional)", ["Todos"] + (list_alumnos_by_grupo(g_pr) if g_pr!="Todos" else []), key="j_pr_alumno")
        
            if prof == "Todos":
                # ======= RANKING DE PROFESORES =======
                df_rank = ranking_profesores(f_ini_p, f_fin_p, estado=estado_p, grupo=g_pr, alumno=a_pr)
                if df_rank.empty:
                    st.info("No hay datos con esos filtros.")
                else:
                    st.dataframe(df_rank, use_container_width=True)
        
                    # PDF (ranking)
                    if HAS_REPORTLAB:
                        titulo = f"Ranking de profesores ({f_ini_p.strftime('%d/%m/%Y')} – {f_fin_p.strftime('%d/%m/%Y')})"
                        if estado_p in ("pendiente","cerrado"): titulo += f" · estado={estado_p}"
                        if g_pr != "Todos": titulo += f" · grupo={g_pr}"
                        if a_pr != "Todos": titulo += f" · alumno={a_pr}"
                        pdf_rank = df_to_pdf_bytes(df_rank, title=titulo)
                        st.download_button(
                            "📄 PDF (ranking)",
                            data=pdf_rank,
                            file_name=f"ranking_profesores_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.pdf",
                            mime="application/pdf",
                            key="j_pr_rank_pdf",
                            use_container_width=True
                        )
        
                    # Excel (ranking)
                    xls = df_to_excel_bytes(df_rank, sheet_name="Ranking_profes")
                    st.download_button(
                        "⬇️ Excel (.xlsx) (ranking)",
                        data=xls,
                        file_name=f"ranking_profesores_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="j_pr_rank_xlsx",
                        use_container_width=True
                    )
            else:
                # ======= HISTORIAL DE UN PROFESOR =======
                row_prof = get_user_by_name(prof)
                if not row_prof:
                    st.error("No se encontró el usuario seleccionado.")
                else:
                    teacher_id = row_prof[0]
                    df_pr = filter_teacher_incidents(
                        teacher_id=teacher_id,
                        start=f_ini_p, end=f_fin_p,
                        estado=estado_p, grupo=g_pr, alumno=a_pr
                    )
        
                    if df_pr.empty:
                        st.info("No hay partes con esos filtros.")
                    else:
                        st.dataframe(df_pr, use_container_width=True)
        
                        # Excel (historial)
                        xls = df_to_excel_bytes(df_pr, sheet_name="Historial_prof")
                        st.download_button(
                            "⬇️ Excel (.xlsx) (historial)",
                            data=xls,
                            file_name=f"historial_prof_{prof.replace(' ','_')}_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="j_pr_xlsx",
                            use_container_width=True
                        )
        
                        # Normalizar 'Hora' si faltase o viene como 'Franja'
                        df_pr_pdf = df_pr.copy()
                        if "Hora" not in df_pr_pdf.columns and "Franja" in df_pr_pdf.columns:
                            df_pr_pdf.rename(columns={"Franja": "Hora"}, inplace=True)
                        elif "Hora" not in df_pr_pdf.columns:
                            df_pr_pdf["Hora"] = ""
        
                        # PDF (historial del profesor)
                        if HAS_REPORTLAB:
                            pdf_prof = teacher_report_pdf(df_pr_pdf.assign(ID=df_pr_pdf.index), prof)
                            if pdf_prof and len(pdf_prof) > 0:
                                st.download_button(
                                    "📄 PDF (historial del profesor)",
                                    data=pdf_prof,
                                    file_name=f"historial_prof_{prof.replace(' ','_')}_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.pdf",
                                    mime="application/pdf",
                                    key="j_pr_hist_pdf",
                                    use_container_width=True
                                )

        # ----- TAB 5: Pendientes (Jefatura) -----
        with tabs[5]:
            st.subheader("📬 Partes pendientes de revisar")
        
            # ✅ Mostrar mensaje de cierre persistido tras refresco
            pend_msg = st.session_state.pop("pend_success_msg", None)
            if pend_msg:
                st.success(pend_msg)
        
            pendientes = list_pending_incidents()
            st.caption(f"Pendientes: **{len(pendientes)}**")
            if not pendientes:
                st.success("No hay partes pendientes. ✅")
            else:
                # Construimos opciones con todos los campos necesarios para mostrar y para cambiar gravedad_inicial si se desea
                opciones = []
                # rows: (iid, prof, grupo, alumno, f, h, desc, grav_ini, created_at)
                for (iid, prof, grupo, alumno, f, h, desc, grav_ini, created_at) in pendientes:
                    label = f"#{iid} · {f} {h} · {alumno} ({grupo}) · {prof} · [inicial: {grav_ini}]"
                    # Metemos toda la tupla que necesitamos en la opción
                    opciones.append((iid, label, desc, grav_ini, prof, grupo, alumno, f, h))
        
                # Nota: guardamos en session la selección previa para no perderla tras cambios
                sel = st.selectbox(
                    "Selecciona un parte",
                    opciones,
                    format_func=lambda x: x[1],
                    key="pend_sel"
                )
        
                if sel:
                    # Desempaquetamos la selección actual
                    sel_id, sel_label, sel_desc, sel_grav_ini, sel_prof, sel_grupo, sel_alumno, sel_fecha, sel_hora = sel
        
                    # Descripción del parte
                    st.markdown("**Descripción del parte:**")
                    st.write(sel_desc)
                    st.markdown("---")
        
                    # =========== SECCIÓN: Opcional - Cambiar gravedad INICIAL ===========
                    st.markdown("#### ⚠️ ¿Deseas **modificar** la **gravedad inicial**?")
                    st.caption("Por defecto, no se cambia. Marca la casilla solo si necesitas corregir el valor de la gravedad **inicial**.")
                    c_mod_toggle = st.checkbox("Quiero cambiar la **gravedad inicial** de este parte", key=f"pend_edit_ini_toggle_{sel_id}")
        
                    new_grav_ini = None
                    confirm_change_ini = False
        
                    if c_mod_toggle:
                        st.info(f"Gravedad inicial actual: **{sel_grav_ini}**")
                        st.markdown("**Selecciona la nueva gravedad inicial** (elige una):")
                        new_grav_ini = gravedad_selector(f"pend_edit_ini_{sel_id}", default=None, show_helper_msg=False)
        
                        # Ayuda si no se ha elegido bien
                        if new_grav_ini not in ("leve", "grave", "muy grave"):
                            st.warning("Selecciona exactamente **una** gravedad inicial (deja solo un tick).")
        
                        # Confirmación (obligatoria si pretende guardarse el cambio)
                        confirm_change_ini = st.checkbox(
                            "✅ Confirmo que **QUIERO** cambiar la gravedad **inicial**",
                            key=f"pend_edit_ini_confirm_{sel_id}"
                        )
                        st.caption("Esta confirmación evita cambios accidentales. Desmarca la opción si no deseas modificarla.")
        
                    st.markdown("---")
        
                    # =========== SECCIÓN: Cierre - Gravedad FINAL ===========
                    st.markdown("**Gravedad final (obligatoria para cerrar)**")
                    grav_final = gravedad_selector(f"pend_final_{sel_id}", default=None)
                    disabled_close = grav_final not in ("leve", "grave", "muy grave")
        
                    # ÚNICO botón de acción: Cerrar parte
                    if st.button("✅ Cerrar parte", key=f"pend_cerrar_{sel_id}", disabled=disabled_close, use_container_width=True):
                        # Si quiere modificar la gravedad INICIAL, comprobar confirmación y validez
                        if c_mod_toggle:
                            if new_grav_ini not in ("leve", "grave", "muy grave"):
                                st.error("Para cambiar la **gravedad inicial**, debes seleccionar exactamente una opción.")
                                st.stop()
                            if not confirm_change_ini:
                                st.error("Debes confirmar que **quieres** cambiar la gravedad **inicial**.")
                                st.stop()
                            # Ejecutar el cambio de gravedad inicial
                            try:
                                with get_conn() as conn:
                                    conn.execute("UPDATE incidents SET gravedad_inicial=? WHERE id=?", (new_grav_ini, sel_id))
                                    conn.commit()
                            except Exception as ex:
                                st.error(f"No se pudo actualizar la gravedad inicial: {ex}")
                                st.stop()
        
                        # Cerrar el parte (establece gravedad_final y marca como cerrado)
                        ok, msg = close_incident(sel_id, grav_final, usuario["id"], usuario["name"])
                        if ok:
                            # ✅ Mantenerse en esta pestaña y mostrar mensaje tras refresco
                            st.session_state["pend_success_msg"] = msg
                            st.rerun()
                        else:
                            st.error(msg)
        
                    # Estado de ayuda si falta gravedad final
                    if disabled_close:
                        st.warning("Debes seleccionar exactamente **una** gravedad **final** para poder cerrar el parte.")

        # ----- TAB 6: Estadísticas (Jefatura) -----
        with tabs[6]:
            st.subheader("📊 Estadísticas (Jefatura)")
            colf1, colf2, colf3 = st.columns([1,1,2])
            with colf1:
                f_ini = st.date_input("Desde", value=school_year_start(), key="stats_ini")
            with colf2:
                f_fin = st.date_input("Hasta", value=date.today(), key="stats_fin")
            with colf3:
                grupos_opt = ["Todos"] + list_grupos()
                grupo_fil = st.selectbox("Grupo", grupos_opt, key="stats_grupo")
                alumnos_fil = ["Todos"] + (list_alumnos_by_grupo(grupo_fil) if grupo_fil != "Todos" else [])
                alumno_fil = st.selectbox("Alumno", alumnos_fil, key="stats_alumno")

            profs_opt = ["Todos"] + list_profesor_names()
            profesor_fil = st.selectbox("Profesor", profs_opt, key="stats_profesor")

            dfc = filter_closed_incidents(f_ini, f_fin, grupo_fil, alumno_fil)

            if dfc.empty:
                st.info("No hay partes cerrados con esos filtros.")
            else:
                st.dataframe(dfc, use_container_width=True)
                st.markdown("---")
                st.metric("Partes cerrados", len(dfc))

                # Informe por ALUMNO (PDF)
                if HAS_REPORTLAB and grupo_fil != "Todos" and alumno_fil != "Todos":
                    pdf_alumno = student_report_pdf(dfc, alumno=alumno_fil, grupo=grupo_fil)
                    if pdf_alumno and len(pdf_alumno) > 0:
                        st.download_button("📄 Exportar informe del alumno a PDF",
                            data=pdf_alumno,
                            file_name=f"informe_{alumno_fil.replace(' ','_')}_{date.today().isoformat()}.pdf",
                            mime="application/pdf", key="stats_pdf_alumno", use_container_width=True)

                # Consulta por profesor
                st.markdown("### 👨‍🏫 Consulta por profesor")
                if profesor_fil == "Todos":
                    rank_prof = (
                        dfc.groupby("Profesor")
                           .size()
                           .sort_values(ascending=False)
                           .reset_index(name="Partes")
                    )
                    if rank_prof.empty:
                        st.info("No hay datos para el ranking de profesores.")
                    else:
                        st.dataframe(rank_prof, use_container_width=True)
                        xls = df_to_excel_bytes(rank_prof, sheet_name="Ranking_prof")
                        st.download_button("⬇️ Exportar ranking profesores (Excel)",
                            data=xls,
                            file_name=f"ranking_profesores_{f_ini.isoformat()}_{f_fin.isoformat()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="stats_prof_rank_xlsx", use_container_width=True)
                        if HAS_REPORTLAB:
                            pdf_prof_rank = df_to_pdf_bytes(rank_prof, title=f"Ranking profesores ({f_ini.strftime('%d/%m/%Y')} – {f_fin.strftime('%d/%m/%Y')})")
                            st.download_button("📄 Exportar ranking profesores (PDF)",
                                data=pdf_prof_rank,
                                file_name=f"ranking_profesores_{f_ini.isoformat()}_{f_fin.isoformat()}.pdf",
                                mime="application/pdf", key="stats_prof_rank_pdf", use_container_width=True)
                else:
                    df_prof = dfc[dfc["Profesor"] == profesor_fil].copy()
                    total_prof = len(df_prof)
                    st.metric(f"Partes del profesor {profesor_fil}", total_prof)
                    if df_prof.empty:
                        st.info("No hay partes del profesor con los filtros seleccionados.")
                    else:
                        # Normalización de Hora para el PDF si se descarga
                        if "Hora" not in df_prof.columns:
                            df_prof["Hora"] = ""
                        cols_hist = ["Fecha","Hora","Grupo","Alumno","Descripción","Gravedad final"]
                        st.dataframe(df_prof[cols_hist], use_container_width=True)
                        xls = df_to_excel_bytes(df_prof[cols_hist], sheet_name="Historial_prof")
                        st.download_button("⬇️ Exportar historial del profesor (Excel)",
                            data=xls,
                            file_name=f"historial_prof_{profesor_fil.replace(' ','_')}_{f_ini.isoformat()}_{f_fin.isoformat()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="stats_prof_hist_xlsx", use_container_width=True)
                        if HAS_REPORTLAB:
                            pdf_prof = teacher_report_pdf(df_prof.assign(ID=df_prof.index), profesor_fil)
                            st.download_button("📄 Exportar informe del profesor (PDF)",
                                data=pdf_prof,
                                file_name=f"informe_prof_{profesor_fil.replace(' ','_')}_{date.today().isoformat()}.pdf",
                                mime="application/pdf", key="stats_prof_hist_pdf", use_container_width=True)

                if HAS_REPORTLAB:
                    titulo = "Incidencias cerradas — tabla filtrada"
                    if grupo_fil != "Todos": titulo += f" — {grupo_fil}"
                    if alumno_fil != "Todos": titulo += f" — {alumno_fil}"
                    titulo += f" ({f_ini.strftime('%d/%m/%Y')} – {f_fin.strftime('%d/%m/%Y')})"
                    pdf_stats = df_to_pdf_bytes(dfc.drop(columns=["_Fecha"], errors="ignore"), title=titulo)
                    st.download_button("📄 Exportar tabla a PDF", data=pdf_stats,
                        file_name=f"incidencias_cerradas_{f_ini.isoformat()}_{f_fin.isoformat()}.pdf",
                        mime="application/pdf", key="stats_pdf", use_container_width=True)
                xls = df_to_excel_bytes(dfc, sheet_name="Incidencias_cerradas")
                st.download_button("⬇️ Exportar tabla (Excel)",
                    data=xls,
                    file_name=f"incidencias_cerradas_{f_ini.isoformat()}_{f_fin.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="stats_xlsx", use_container_width=True)

        # ----- TAB 7: Gráficos (Jefatura) -----
        with tabs[7]:
            st.subheader("📈 Gráficos (Jefatura)")
            colf1, colf2, colf3 = st.columns([1,1,2])
            with colf1:
                f_ini_g = st.date_input("Desde", value=school_year_start(), key="charts_ini")
            with colf2:
                f_fin_g = st.date_input("Hasta", value=date.today(), key="charts_fin")
            with colf3:
                grupos_opt_g = ["Todos"] + list_grupos()
                grupo_g = st.selectbox("Grupo", grupos_opt_g, key="charts_grupo")
                alumnos_g = ["Todos"] + (list_alumnos_by_grupo(grupo_g) if grupo_g != "Todos" else [])
                alumno_g = st.selectbox("Alumno", alumnos_g, key="charts_alumno")

            dfc_g = filter_closed_incidents(f_ini_g, f_fin_g, grupo_g, alumno_g)
            if dfc_g.empty:
                st.info("No hay partes cerrados con esos filtros.")
            else:
                graf = st.selectbox(
                    "Selecciona gráfico",
                    ["Número de partes por grupos", "Número de partes por semanas", "Número de partes por meses"],
                    key="charts_sel"
                )
                dfc_g["_Fecha"] = pd.to_datetime(dfc_g["Fecha"], errors="coerce")
                if graf == "Número de partes por grupos":
                    grcount = dfc_g["Grupo"].value_counts().sort_values(ascending=False)
                    st.bar_chart(grcount, use_container_width=True)
                elif graf == "Número de partes por semanas":
                    dfc_g["_Semana"] = dfc_g["_Fecha"].dt.strftime("%G-W%V")
                    wcount = dfc_g["_Semana"].value_counts().sort_index()
                    st.bar_chart(wcount, use_container_width=True)
                elif graf == "Número de partes por meses":
                    dfc_g["_Mes"] = dfc_g["_Fecha"].dt.strftime("%Y-%m")
                    mcount = dfc_g["_Mes"].value_counts().sort_index()
                    st.bar_chart(mcount, use_container_width=True)

        # ----- TAB 8: Usuarios (Jefatura) -----
        with tabs[8]:
            st.subheader("👥 Gestión de usuarios")

            st.markdown("### ➕ Crear usuario")
            with st.form("users_form_create", clear_on_submit=True):
                colu1, colu2, colu3 = st.columns([2,2,1])
                with colu1: u_name = st.text_input("Nombre completo", key="users_name")
                with colu2: u_email = st.text_input("Email", key="users_email")
                with colu3: u_role = st.selectbox("Rol", ["profesor","jefe","director","convivencia"], key="users_role")
                if st.form_submit_button("Crear", use_container_width=True, key="users_create"):
                    ok, msg = create_user(u_name, u_email, u_role)
                    (st.success if ok else st.error)(msg)

            st.markdown("---")
            st.markdown("### 📥 Importar profesores desde Excel")
            st.caption("Excel con columnas: **Nombre**, **Email** (rol: profesor).")
            up_prof = st.file_uploader("Selecciona Excel de profesores", type=["xlsx"], key="users_up_prof")
            if st.button("Importar profesores", key="users_btn_import", use_container_width=True):
                if up_prof is None:
                    st.error("Selecciona un Excel con columnas: Nombre, Email.")
                else:
                    try:
                        df_p = pd.read_excel(up_prof, engine="openpyxl")
                        ins, skip = import_profesores_from_excel(df_p)
                        st.success(f"Importación completada. Insertados: {ins}, ya existentes: {skip}.")
                    except Exception as ex:
                        st.error(f"No se pudo importar: {ex}")

            st.markdown("---")
            st.markdown("### 🗂 Usuarios")
            users = list_users()
            if not users:
                st.info("No hay usuarios.")
            else:
                hdr = st.columns([3,3,2,2,6])
                hdr[0].markdown("**Nombre**"); hdr[1].markdown("**Email**")
                hdr[2].markdown("**Rol**"); hdr[3].markdown("**Estado**"); hdr[4].markdown("**Acciones**")
                rol_map_short = {"jefe": "Jefatura", "profesor": "Profesor", "director": "Director", "convivencia": "Convivencia"}

                for (uid, name, email, role, active, pw_hash) in users:
                    cols = st.columns([3,3,2,2,6])
                    cols[0].write(name)
                    cols[1].write(email)
                    cols[2].write(rol_map_short.get(role, role))
                    cols[3].write("Activo ✅" if active==1 else "Suspendido ⛔")

                    with cols[4]:
                        c1, c2, c3, c4, c5 = st.columns([1,1,1,3,1])
                        if active == 1:
                            if c1.button("⏸️", key=f"users_susp_{uid}", help="Suspender usuario"):
                                if uid == usuario["id"]:
                                    st.error("No puedes suspender tu propia cuenta.")
                                else:
                                    set_user_active(uid, False); st.rerun()
                        else:
                            if c1.button("▶️", key=f"users_react_{uid}", help="Reactivar usuario"):
                                set_user_active(uid, True); st.rerun()

                        if c2.button("🗑️", key=f"users_del_{uid}", help="Eliminar usuario"):
                            if uid == usuario["id"]:
                                st.error("No puedes eliminar tu propia cuenta.")
                            else:
                                delete_user(uid); st.rerun()

                        if c3.button("🔁", key=f"users_reset_{uid}", help="Resetear contraseña (pedirá nueva al entrar)"):
                            with get_conn() as conn:
                                conn.execute("UPDATE users SET password_hash=NULL WHERE id=?", (uid,))
                                conn.commit()
                            st.success("Contraseña reiniciada. Pedirá nueva al próximo acceso.")

                        all_roles = ["profesor","jefe","director","convivencia"]
                        try:
                            idx_role = all_roles.index(role)
                        except ValueError:
                            idx_role = 0
                        new_role_sel = c4.selectbox(
                            "Rol",
                            all_roles,
                            index=idx_role,
                            key=f"users_role_select_{uid}",
                            label_visibility="collapsed"
                        )

                        if c5.button("Guardar", key=f"users_role_save_{uid}", help="Guardar rol seleccionado"):
                            if uid == usuario["id"]:
                                st.error("No puedes cambiar tu propio rol aquí.")
                            elif new_role_sel == role:
                                st.info("El usuario ya tiene ese rol.")
                            else:
                                ok, msg = set_user_role(uid, new_role_sel)
                                (st.success if ok else st.error)(msg)
                                if ok: st.rerun()

    # =============== DIRECTOR ===============
    elif rol == "director":
        tabs = st.tabs([
            "📝 Nuevo parte",
            "🔥 Ranking alumnos",
            "📚 Historial de alumnos",
            "👨‍🏫 Historial de profesores",
        ])

        # ----- TAB 0: Nuevo parte (Director) -----
        with tabs[0]:
            st.subheader("📝 Nuevo parte")
            grupos = list_grupos()
            if not grupos: st.warning("No hay grupos cargados.")
            else:
                col_g, col_a = st.columns([1,2])
                grupo_sel = col_g.selectbox("Grupo", options=grupos, key="d_grupo")
                if "d_grupo_prev" not in st.session_state or st.session_state["d_grupo_prev"] != grupo_sel:
                    st.session_state["d_alumno"] = None; st.session_state["d_grupo_prev"] = grupo_sel
                alumnos = list_alumnos_by_grupo(grupo_sel)
                alumno_sel = col_a.selectbox("Alumno", options=alumnos if alumnos else [], key="d_alumno")
                with st.form("d_form_parte"):
                    col1, col2 = st.columns(2)
                    with col1: 
                        fecha_sel = st.date_input("Fecha", value=date.today(), max_value=date.today(), key="d_fecha")
                    with col2: franja_sel = st.selectbox("Franja horaria", FRANJAS, key="d_franja")
                    st.markdown("**Gravedad (inicial)**"); grav_ini = gravedad_selector("d_grav_ini", default=None)
                    descripcion = st.text_area("Descripción (obligatoria)", key="d_desc")
                    enviar = st.form_submit_button("Enviar parte a Jefatura", use_container_width=True)
                if enviar:
                    if not alumnos or not alumno_sel or not grupo_sel: st.error("Grupo y alumno son obligatorios.")
                    elif not descripcion or not descripcion.strip(): st.error("La descripción es obligatoria.")
                    elif grav_ini not in ("leve","grave","muy grave"): st.error("Selecciona exactamente una gravedad.")
                    else:
                        ok, msg = create_incident(
                            teacher_id=usuario["id"], teacher_name=usuario["name"],
                            grupo=grupo_sel, alumno=alumno_sel, fecha=fecha_sel, franja=franja_sel,
                            descripcion=descripcion.strip(), gravedad_inicial=grav_ini
                        )
                        if ok:
                            reset_nuevo_parte_form("d_")
                            go_home_after_submit(msg); st.rerun()
                        else:
                            st.error(msg)

        # ----- TAB 1: Ranking alumnos (Director) -----
        with tabs[1]:
            st.subheader("🔥 Ranking alumnos")
            c1, c2, c3, c4 = st.columns([1,1,1,1.5])
            with c1:
                f_ini_rk = st.date_input("Desde", value=school_year_start(), key="d_rk_ini")
            with c2:
                f_fin_rk = st.date_input("Hasta", value=date.today(), key="d_rk_fin")
            with c3:
                g_rk = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="d_rk_grupo")
            with c4:
                solo_cerr = st.checkbox("Solo cerrados", value=True, key="d_rk_cerr")
                pond_grav = st.checkbox("Ponderar gravedad (L=1, G=2, MG=3)", value=True, key="d_rk_pond")
        
            df_rk = ranking_disruptivos(
                f_ini_rk, f_fin_rk,
                grupo_filtro=g_rk,
                solo_cerrados=solo_cerr,
                ponderar_gravedad=pond_grav
            )
        
            if df_rk.empty:
                st.info("No hay datos.")
            else:
                st.dataframe(df_rk, use_container_width=True)
        
                # === PDF (igual que en Jefatura) ===
                if HAS_REPORTLAB:
                    titulo = "Ranking alumnos más disruptivos"
                    if g_rk != "Todos":
                        titulo += f" — {g_rk}"
                    titulo += f" ({f_ini_rk.strftime('%d/%m/%Y')} – {f_fin_rk.strftime('%d/%m/%Y')})"
                    if solo_cerr:
                        titulo += " · solo cerrados"
                    if pond_grav:
                        titulo += " · ponderado por gravedad"
        
                    pdf_rk = df_to_pdf_bytes(df_rk, title=titulo)
                    st.download_button(
                        "📄 Exportar a PDF",
                        data=pdf_rk,
                        file_name=f"ranking_disruptivos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.pdf",
                        mime="application/pdf",
                        key="d_rk_pdf",
                        use_container_width=True
                    )
        
                # === Excel ===
                xls = df_to_excel_bytes(df_rk, sheet_name="Ranking")
                st.download_button(
                    "⬇️ Excel (.xlsx)",
                    data=xls,
                    file_name=f"ranking_alumnos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="d_rk_xlsx",
                    use_container_width=True
                )

        # ----- TAB 2: Historial de alumnos (Director) -----
        with tabs[2]:
            st.subheader("📚 Historial de alumnos")
            c1, c2, c3 = st.columns([1,1,2])
            with c1: f_ini_a = st.date_input("Desde", value=school_year_start(), key="d_al_ini")
            with c2: f_fin_a = st.date_input("Hasta", value=date.today(), key="d_al_fin")
            with c3:
                g_al = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="d_al_grupo")
                a_opts = ["Todos"] + (list_alumnos_by_grupo(g_al) if g_al != "Todos" else [])
                a_sel = st.selectbox("Alumno", a_opts, key="d_al_alumno")
            df_al = filter_closed_incidents(f_ini_a, f_fin_a, g_al, a_sel)
            if df_al.empty:
                st.info("No hay partes cerrados con esos filtros.")
            else:
                st.dataframe(df_al, use_container_width=True)

                # PDF con nuevo formato (7 columnas)
                if HAS_REPORTLAB:
                    pdf_custom = student_report_pdf(
                        df_al,
                        alumno=(a_sel if a_sel and a_sel != "Todos" else None),
                        grupo=(g_al if g_al and g_al != "Todos" else None)
                    )
                    st.download_button(
                        "📄 Exportar historial (PDF, 7 columnas)",
                        data=pdf_custom,
                        file_name=f"historial_alumnos_{g_al}_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.pdf",
                        mime="application/pdf", key="j_al_pdf_custom", use_container_width=True
                    )
                
                if HAS_REPORTLAB and g_al != "Todos" and a_sel != "Todos":
                    pdf_al = student_report_pdf(df_al, alumno=a_sel, grupo=g_al)
                    st.download_button("📄 Informe del alumno (PDF)", data=pdf_al,
                        file_name=f"informe_{a_sel.replace(' ','_')}_{date.today().isoformat()}.pdf",
                        mime="application/pdf", key="d_al_pdf", use_container_width=True)
                xls = df_to_excel_bytes(df_al, sheet_name="Historial_alumnos")
                st.download_button("⬇️ Excel (.xlsx)", data=xls,
                    file_name=f"historial_alumnos_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="d_al_xlsx", use_container_width=True)

        # ----- TAB 3: Historial de profesores (Director)
        with tabs[3]:
            st.subheader("👨‍🏫 Historial de profesores")
            c1, c2, c3 = st.columns([1,1,2])
            with c1: f_ini_p = st.date_input("Desde", value=school_year_start(), key="d_pr_ini")
            with c2: f_fin_p = st.date_input("Hasta", value=date.today(), key="d_pr_fin")
            with c3: estado_p = st.selectbox("Estado", ["Todos","pendiente","cerrado"], key="d_pr_estado")
            prof_opts = ["Todos"] + list_profesor_names()
            prof = st.selectbox("Profesor", prof_opts, index=0, key="d_pr_prof")
            g_pr = st.selectbox("Grupo (opcional)", ["Todos"] + list_grupos(), key="d_pr_grupo")
            a_pr = st.selectbox("Alumno (opcional)", ["Todos"] + (list_alumnos_by_grupo(g_pr) if g_pr!="Todos" else []), key="d_pr_alumno")
        
            if prof == "Todos":
                # ======= RANKING DE PROFESORES =======
                df_rank = ranking_profesores(f_ini_p, f_fin_p, estado=estado_p, grupo=g_pr, alumno=a_pr)
                if df_rank.empty:
                    st.info("No hay datos con esos filtros.")
                else:
                    st.dataframe(df_rank, use_container_width=True)
        
                    # Excel (ranking)
                    xls = df_to_excel_bytes(df_rank, sheet_name="Ranking_profes")
                    st.download_button(
                        "⬇️ Excel (.xlsx) (ranking)",
                        data=xls,
                        file_name=f"ranking_profesores_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="d_pr_rank_xlsx",
                        use_container_width=True
                    )
        
                    # PDF (ranking)
                    if HAS_REPORTLAB:
                        titulo = f"Ranking de profesores ({f_ini_p.strftime('%d/%m/%Y')} – {f_fin_p.strftime('%d/%m/%Y')})"
                        if estado_p in ("pendiente","cerrado"): titulo += f" · estado={estado_p}"
                        if g_pr != "Todos": titulo += f" · grupo={g_pr}"
                        if a_pr != "Todos": titulo += f" · alumno={a_pr}"
                        pdf_rank = df_to_pdf_bytes(df_rank, title=titulo)
                        st.download_button(
                            "📄 PDF (ranking)",
                            data=pdf_rank,
                            file_name=f"ranking_profesores_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.pdf",
                            mime="application/pdf",
                            key="d_pr_rank_pdf",
                            use_container_width=True
                        )
            else:
                # ======= HISTORIAL DE UN PROFESOR =======
                row_prof = get_user_by_name(prof)
                if not row_prof:
                    st.error("No se encontró el usuario seleccionado.")
                else:
                    teacher_id = row_prof[0]
                    df_pr = filter_teacher_incidents(
                        teacher_id=teacher_id,
                        start=f_ini_p, end=f_fin_p,
                        estado=estado_p, grupo=g_pr, alumno=a_pr
                    )
        
                    if df_pr.empty:
                        st.info("No hay partes con esos filtros.")
                    else:
                        st.dataframe(df_pr, use_container_width=True)
        
                        # Excel (historial)
                        xls = df_to_excel_bytes(df_pr, sheet_name="Historial_prof")
                        st.download_button(
                            "⬇️ Excel (.xlsx) (historial)",
                            data=xls,
                            file_name=f"historial_prof_{prof.replace(' ','_')}_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="d_pr_xlsx",
                            use_container_width=True
                        )
        
                        # Normalizar 'Hora' si faltase o viene como 'Franja'
                        df_pr_pdf = df_pr.copy()
                        if "Hora" not in df_pr_pdf.columns and "Franja" in df_pr_pdf.columns:
                            df_pr_pdf.rename(columns={"Franja": "Hora"}, inplace=True)
                        elif "Hora" not in df_pr_pdf.columns:
                            df_pr_pdf["Hora"] = ""
        
                        # PDF (historial del profesor)
                        if HAS_REPORTLAB:
                            pdf_prof = teacher_report_pdf(df_pr_pdf.assign(ID=df_pr_pdf.index), prof)
                            if pdf_prof and len(pdf_prof) > 0:
                                st.download_button(
                                    "📄 PDF (historial del profesor)",
                                    data=pdf_prof,
                                    file_name=f"historial_prof_{prof.replace(' ','_')}_{f_ini_p.isoformat()}_{f_fin_p.isoformat()}.pdf",
                                    mime="application/pdf",
                                    key="d_pr_hist_pdf",
                                    use_container_width=True
                                )

    # =============== CONVIVENCIA ===============
    elif rol == "convivencia":
        tabs = st.tabs([
            "📝 Nuevo parte",
            "📜 Mi historial",
            "🔥 Ranking alumnos",
            "📚 Historial de alumnos",
        ])

        # ----- TAB 0: Nuevo parte (Convivencia) -----
        with tabs[0]:
            st.subheader("📝 Nuevo parte")
            grupos = list_grupos()
            if not grupos: st.warning("No hay grupos cargados.")
            else:
                col_g, col_a = st.columns([1,2])
                grupo_sel = col_g.selectbox("Grupo", options=grupos, key="c_grupo")
                if "c_grupo_prev" not in st.session_state or st.session_state["c_grupo_prev"] != grupo_sel:
                    st.session_state["c_alumno"] = None; st.session_state["c_grupo_prev"] = grupo_sel
                alumnos = list_alumnos_by_grupo(grupo_sel)
                alumno_sel = col_a.selectbox("Alumno", options=alumnos if alumnos else [], key="c_alumno")
                with st.form("c_form_parte"):
                    col1, col2 = st.columns(2)
                    with col1: fecha_sel = st.date_input("Fecha", value=date.today(), max_value=date.today(), key="c_fecha")
                    with col2: franja_sel = st.selectbox("Franja horaria", FRANJAS, key="c_franja")
                    st.markdown("**Gravedad (inicial)**"); grav_ini = gravedad_selector("c_grav_ini", default=None)
                    descripcion = st.text_area("Descripción (obligatoria)", key="c_desc")
                    enviar = st.form_submit_button("Enviar parte a Jefatura", use_container_width=True)
                if enviar:
                    if not alumnos or not alumno_sel or not grupo_sel:
                        st.error("Grupo y alumno son obligatorios.")
                    elif not descripcion or not descripcion.strip():
                        st.error("La descripción es obligatoria.")
                    elif grav_ini not in ("leve","grave","muy grave"):
                        st.error("Selecciona exactamente una gravedad.")
                    else:
                        ok, msg = create_incident(
                            teacher_id=usuario["id"], teacher_name=usuario["name"],
                            grupo=grupo_sel, alumno=alumno_sel, fecha=fecha_sel, franja=franja_sel,
                            descripcion=descripcion.strip(), gravedad_inicial=grav_ini
                        )
                        if ok:
                            reset_nuevo_parte_form("c_")
                            go_home_after_submit(msg); st.rerun()
                        else:
                            st.error(msg)

        # ----- TAB 1: Mi historial (Convivencia) ----
        with tabs[1]:
            st.subheader("📜 Mi historial")
            
            # Filtros
            colh1, colh2, colh3, colh4 = st.columns([1,1,1,1.5])
            with colh1: f_ini_h = st.date_input("Desde", value=school_year_start(), key="c_hist_ini")
            with colh2: f_fin_h = st.date_input("Hasta", value=date.today(), key="c_hist_fin")
            with colh3: estado_sel = st.selectbox("Estado", ["Todos","pendiente","cerrado"], index=0, key="c_hist_estado")
            with colh4:
                g_sel = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="c_hist_grupo")
                a_sel = st.selectbox("Alumno", ["Todos"] + (list_alumnos_by_grupo(g_sel) if g_sel!="Todos" else []), key="c_hist_alumno")
            
            # Obtener historial
            df_hist = filter_teacher_incidents(teacher_id=usuario["id"], start=f_ini_h, end=f_fin_h, estado=estado_sel, grupo=g_sel, alumno=a_sel)
            if df_hist.empty: st.info("No hay partes en tu historial con esos filtros.")
            else:
                st.metric("Número de partes", len(df_hist))
                st.dataframe(df_hist, use_container_width=True)
                
                # PDF igual al profesor
                if HAS_REPORTLAB:
                    df_for_pdf = df_hist.copy()

                    # Normalizar 'Hora' si procede (algunos listados la traen como 'Franja')
                    if "Hora" not in df_for_pdf.columns and "Franja" in df_for_pdf.columns:
                        df_for_pdf.rename(columns={"Franja": "Hora"}, inplace=True)
                    elif "Hora" not in df_for_pdf.columns:
                        df_for_pdf["Hora"] = ""

                    # teacher_report_pdf necesita columna ID para ordenar correctamente
                    df_for_pdf = df_for_pdf.assign(ID=df_for_pdf.index)

                    pdf_bytes = teacher_report_pdf(df_for_pdf, usuario["name"])

                    st.download_button(
                        "📄 Exportar mi historial (PDF)",
                        data=pdf_bytes,
                        file_name=f"mi_historial_{usuario['name'].replace(' ', '_')}_{f_ini_h.isoformat()}_{f_fin_h.isoformat()}.pdf",
                        mime="application/pdf",
                        key="c_hist_pdf",
                        use_container_width=True
                    )
                # Exportar EXCEL
                xls = df_to_excel_bytes(df_hist, sheet_name="Mi_historial")
                st.download_button("⬇️ Exportar a Excel (.xlsx)", data=xls,
                    file_name=f"mi_historial_{f_ini_h.isoformat()}_{f_fin_h.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="c_hist_xlsx", use_container_width=True)

        # ----- TAB 2: Ranking alumnos (Convivencia) ----
        with tabs[2]:
            st.subheader("🔥 Ranking alumnos")
            c1, c2, c3, c4 = st.columns([1,1,1,1.5])
            with c1:
                f_ini_rk = st.date_input("Desde", value=school_year_start(), key="c_rk_ini")
            with c2:
                f_fin_rk = st.date_input("Hasta", value=date.today(), key="c_rk_fin")
            with c3:
                g_rk = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="c_rk_grupo")
            with c4:
                solo_cerr = st.checkbox("Solo cerrados", value=True, key="c_rk_cerr")
                pond_grav = st.checkbox("Ponderar gravedad (L=1, G=2, MG=3)", value=True, key="c_rk_pond")
        
            df_rk = ranking_disruptivos(
                f_ini_rk, f_fin_rk,
                grupo_filtro=g_rk,
                solo_cerrados=solo_cerr,
                ponderar_gravedad=pond_grav
            )
        
            if df_rk.empty:
                st.info("No hay datos.")
            else:
                st.dataframe(df_rk, use_container_width=True)
        
                # === PDF (igual que Jefatura/Director) ===
                if HAS_REPORTLAB:
                    titulo = "Ranking alumnos más disruptivos"
                    if g_rk != "Todos":
                        titulo += f" — {g_rk}"
                    titulo += f" ({f_ini_rk.strftime('%d/%m/%Y')} – {f_fin_rk.strftime('%d/%m/%Y')})"
                    if solo_cerr:
                        titulo += " · solo cerrados"
                    if pond_grav:
                        titulo += " · ponderado por gravedad"
        
                    pdf_rk = df_to_pdf_bytes(df_rk, title=titulo)
                    st.download_button(
                        "📄 Exportar a PDF",
                        data=pdf_rk,
                        file_name=f"ranking_disruptivos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.pdf",
                        mime="application/pdf",
                        key="c_rk_pdf",
                        use_container_width=True
                    )
        
                # === Excel (igual que Jefatura/Director) ===
                xls = df_to_excel_bytes(df_rk, sheet_name="Ranking")
                st.download_button(
                    "⬇️ Excel (.xlsx)",
                    data=xls,
                    file_name=f"ranking_alumnos_{g_rk}_{f_ini_rk.isoformat()}_{f_fin_rk.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="c_rk_xlsx",
                    use_container_width=True
                )

        # ----- TAB 3: Historial (Convivencia) ----
        with tabs[3]:
            st.subheader("📚 Historial de alumnos")
            c1, c2, c3 = st.columns([1,1,2])
            with c1: f_ini_a = st.date_input("Desde", value=school_year_start(), key="c_al_ini")
            with c2: f_fin_a = st.date_input("Hasta", value=date.today(), key="c_al_fin")
            with c3:
                g_al = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="c_al_grupo")
                a_opts = ["Todos"] + (list_alumnos_by_grupo(g_al) if g_al != "Todos" else [])
                a_sel = st.selectbox("Alumno", a_opts, key="c_al_alumno")
            df_al = filter_closed_incidents(f_ini_a, f_fin_a, g_al, a_sel)
            if df_al.empty:
                st.info("No hay partes cerrados con esos filtros.")
            else:
                st.dataframe(df_al, use_container_width=True)

                # PDF con nuevo formato (7 columnas)
                if HAS_REPORTLAB:
                    pdf_custom = student_report_pdf(
                        df_al,
                        alumno=(a_sel if a_sel and a_sel != "Todos" else None),
                        grupo=(g_al if g_al and g_al != "Todos" else None)
                    )
                    st.download_button(
                        "📄 Exportar historial (PDF, 7 columnas)",
                        data=pdf_custom,
                        file_name=f"historial_alumnos_{g_al}_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.pdf",
                        mime="application/pdf", key="j_al_pdf_custom", use_container_width=True
                    )
                
                if HAS_REPORTLAB and g_al != "Todos" and a_sel != "Todos":
                    pdf_al = student_report_pdf(df_al, alumno=a_sel, grupo=g_al)
                    st.download_button("📄 Informe del alumno (PDF)", data=pdf_al,
                        file_name=f"informe_{a_sel.replace(' ','_')}_{date.today().isoformat()}.pdf",
                        mime="application/pdf", key="c_al_pdf", use_container_width=True)
                xls = df_to_excel_bytes(df_al, sheet_name="Historial_alumnos")
                st.download_button("⬇️ Excel (.xlsx)", data=xls,
                    file_name=f"historial_alumnos_{f_ini_a.isoformat()}_{f_fin_a.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="c_al_xlsx", use_container_width=True)

    # =============== PROFESOR (por defecto) ===============
    else:
        tabs = st.tabs(["📝 Nuevo parte", "📜 Mi historial"])

        # ----- TAB 0: Nuevo parte (Profesor) ----
        with tabs[0]:
            st.subheader("📝 Nuevo parte")
            grupos = list_grupos()
            if not grupos: st.warning("No hay grupos cargados.")
            else:
                col_g, col_a = st.columns([1,2])
                grupo_sel = col_g.selectbox("Grupo", options=grupos, key="p_grupo_prof")
                if "p_grupo_prev_prof" not in st.session_state or st.session_state["p_grupo_prev_prof"] != grupo_sel:
                    st.session_state["p_alumno_prof"] = None; st.session_state["p_grupo_prev_prof"] = grupo_sel
                alumnos = list_alumnos_by_grupo(grupo_sel)
                alumno_sel = col_a.selectbox("Alumno", options=alumnos if alumnos else [], key="p_alumno_prof")
                with st.form("p_form_parte_prof"):
                    col1, col2 = st.columns(2)
                    with col1: fecha_sel = st.date_input("Fecha", value=date.today(), max_value=date.today(), key="p_fecha_prof")
                    with col2: franja_sel = st.selectbox("Franja horaria", FRANJAS, key="p_franja_prof")
                    st.markdown("**Gravedad (inicial)**"); grav_ini = gravedad_selector("p_grav_ini_prof", default=None)
                    descripcion = st.text_area("Descripción (obligatoria)", key="p_desc_prof")
                    enviar = st.form_submit_button("Enviar parte a Jefatura", use_container_width=True)
                if enviar:
                    if not alumnos or not alumno_sel or not grupo_sel:
                        st.error("Grupo y alumno son obligatorios.")
                    elif not descripcion or not descripcion.strip():
                        st.error("La descripción es obligatoria.")
                    elif grav_ini not in ("leve","grave","muy grave"):
                        st.error("Selecciona exactamente una gravedad.")
                    else:
                        ok, msg = create_incident(
                            teacher_id=usuario["id"], teacher_name=usuario["name"],
                            grupo=grupo_sel, alumno=alumno_sel, fecha=fecha_sel, franja=franja_sel,
                            descripcion=descripcion.strip(), gravedad_inicial=grav_ini
                        )
                        if ok:
                            reset_nuevo_parte_form("p_")
                            go_home_after_submit(msg); st.rerun()
                        else:
                            st.error(msg)

        # ----- TAB 1: Mi historial (Profesor) ----
        with tabs[1]:
            st.subheader("📜 Mi historial")
            colh1, colh2, colh3, colh4 = st.columns([1,1,1,1.5])
            with colh1: f_ini_h = st.date_input("Desde", value=school_year_start(), key="hist_ini")
            with colh2: f_fin_h = st.date_input("Hasta", value=date.today(), key="hist_fin")
            with colh3: estado_sel = st.selectbox("Estado", ["Todos","pendiente","cerrado"], index=0, key="hist_estado")
            with colh4:
                g_sel = st.selectbox("Grupo", ["Todos"] + list_grupos(), key="hist_grupo")
                a_sel = st.selectbox("Alumno", ["Todos"] + (list_alumnos_by_grupo(g_sel) if g_sel!="Todos" else []), key="hist_alumno")
            df_hist = filter_teacher_incidents(teacher_id=usuario["id"], start=f_ini_h, end=f_fin_h, estado=estado_sel, grupo=g_sel, alumno=a_sel)
            if df_hist.empty:
                st.info("No hay partes en tu historial con esos filtros.")
            else:
                st.metric("Número de partes", len(df_hist))
                st.dataframe(df_hist, use_container_width=True)
                # ✅ PDF "Mi historial" (8 columnas especificadas)
                if HAS_REPORTLAB:
                    # Normalizar Hora si hiciera falta
                    if "Hora" not in df_hist.columns and "Franja" in df_hist.columns:
                        df_hist = df_hist.rename(columns={"Franja":"Hora"})
                    elif "Hora" not in df_hist.columns:
                        df_hist["Hora"] = ""
                    pdf_prof = teacher_report_pdf(df_hist.assign(ID=df_hist.index), usuario["name"])
                    st.download_button("📄 Exportar mi historial (PDF)",
                        data=pdf_prof,
                        file_name=f"mi_historial_{usuario['name'].replace(' ','_')}_{f_ini_h.isoformat()}_{f_fin_h.isoformat()}.pdf",
                        mime="application/pdf", key="hist_pdf", use_container_width=True)
                xls = df_to_excel_bytes(df_hist, sheet_name="Mi_historial")
                st.download_button("⬇️ Exportar a Excel (.xlsx)",
                    data=xls,
                    file_name=f"mi_historial_{f_ini_h.isoformat()}_{f_fin_h.isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="hist_xlsx", use_container_width=True)

# ========== BLOQUE 7/7: Entry point ==========

if __name__ == "__main__":
    main()

















