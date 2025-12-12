"""
SQLite persistence layer for the WhatsApp Blast application.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

from . import config
from .models import Contact, LogEntry, ScheduleEntry, Template


class Database:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    number TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    template_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES templates(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )

    # Contact operations
    def list_contacts(self) -> List[Contact]:
        with self._connection() as conn:
            rows = conn.execute("SELECT id, name, number FROM contacts ORDER BY name").fetchall()
        return [Contact(id=row["id"], name=row["name"], number=row["number"]) for row in rows]

    def add_contact(self, name: str, number: str) -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO contacts (name, number) VALUES (?, ?)",
                (name.strip(), normalize_number(number)),
            )
            return cursor.lastrowid

    def update_contact(self, contact_id: int, name: str, number: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE contacts SET name = ?, number = ? WHERE id = ?",
                (name.strip(), normalize_number(number), contact_id),
            )

    def delete_contact(self, contact_id: int) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

    def import_contacts_from_csv(self, csv_path: Path | str) -> int:
        df = pd.read_csv(csv_path)
        if "number" not in df.columns:
            raise ValueError("CSV harus memiliki kolom 'number'")
        df["name"] = df.get("name", "").fillna("")
        inserted = 0
        with self._connection() as conn:
            for _, row in df.iterrows():
                name = str(row["name"]).strip() or "No Name"
                number = normalize_number(str(row["number"]))
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO contacts (name, number) VALUES (?, ?)",
                        (name, number),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    continue
        return inserted

    # Template operations
    def list_templates(self) -> List[Template]:
        with self._connection() as conn:
            rows = conn.execute("SELECT id, title, body FROM templates ORDER BY title").fetchall()
        return [Template(id=row["id"], title=row["title"], body=row["body"]) for row in rows]

    def add_template(self, title: str, body: str) -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO templates (title, body) VALUES (?, ?)",
                (title.strip(), body.strip()),
            )
            return cursor.lastrowid

    def update_template(self, template_id: int, title: str, body: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE templates SET title = ?, body = ? WHERE id = ?",
                (title.strip(), body.strip(), template_id),
            )

    def delete_template(self, template_id: int) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))

    # Schedule operations
    def add_schedule(self, start_time: datetime, template_id: int, status: str = "scheduled") -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO schedules (start_time, template_id, status) VALUES (?, ?, ?)",
                (start_time.isoformat(), template_id, status),
            )
            return cursor.lastrowid

    def list_schedules(self) -> List[ScheduleEntry]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, start_time, template_id, status FROM schedules ORDER BY start_time DESC"
            ).fetchall()
        return [
            ScheduleEntry(
                id=row["id"],
                start_time=datetime.fromisoformat(row["start_time"]),
                template_id=row["template_id"],
                status=row["status"],
            )
            for row in rows
        ]

    def update_schedule_status(self, schedule_id: int, status: str) -> None:
        with self._connection() as conn:
            conn.execute("UPDATE schedules SET status = ? WHERE id = ?", (status, schedule_id))

    def delete_schedule(self, schedule_id: int) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    # Log operations
    def add_log(self, number: str, status: str, message: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO logs (number, status, message, timestamp) VALUES (?, ?, ?, ?)",
                (normalize_number(number), status, message, datetime.utcnow().isoformat()),
            )

    def list_logs(self, limit: int = 200) -> List[LogEntry]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, number, status, message, timestamp FROM logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            LogEntry(
                id=row["id"],
                number=row["number"],
                status=row["status"],
                message=row["message"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]


def normalize_number(number: str) -> str:
    digits = "".join(filter(str.isdigit, number))
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return digits
