# db/connection.py
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Ruta a la base de datos (SQLite por ahora)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "app.db"


@contextmanager
def get_db():
    """
    Context manager para obtener una conexión a la base de datos.
    Uso:
        with get_db() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
