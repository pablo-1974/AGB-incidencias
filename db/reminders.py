# db/reminders.py

from db.connection import get_db
from datetime import date


def get_pending_reminders(today: date):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  r.id,
                  r.incident_id,
                  r.due_date,
                  r.note,
                  i.alumno,
                  i.grupo
                FROM incident_reminders r
                JOIN incidents i ON i.id = r.incident_id
                WHERE r.done = false
                  AND r.due_date <= %s
                ORDER BY r.due_date ASC
                """,
                (today,),
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "incident_id": r[1],
            "fecha": r[2],
            "note": r[3],
            "alumno": r[4],
            "grupo": r[5],
        }
        for r in rows
    ]
