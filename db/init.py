# db/init.py
from db.connection import get_db


def check_db():
    """
    Comprueba que la base de datos es accesible.
    No crea ni modifica tablas.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
