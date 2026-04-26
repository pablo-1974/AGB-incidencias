# db/connection.py
import os
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida en el entorno")


@contextmanager
def get_db():
    """
    Devuelve una conexión PostgreSQL (Neon) con filas como diccionarios.
    """
    conn = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
