# db/connection.py
import os
import psycopg
from contextlib import contextmanager


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida en el entorno")


@contextmanager
def get_db():
    """
    Devuelve una conexión PostgreSQL (Neon).
    Uso:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
