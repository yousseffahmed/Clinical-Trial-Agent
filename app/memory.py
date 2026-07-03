"""SQLite-backed local user preference and fact memory."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .config import settings


class MemoryStore:
    """Small, explicit SQLite repository used by both API and MCP tools."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or settings.memory_db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.db_path), timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        # Schema creation is idempotent, so a missing database is repaired on
        # startup and before every public operation.
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)"
            )

    def save_memory(self, key: str, value: str) -> Dict[str, object]:
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise ValueError("Memory key and value must not be blank.")
        self.init_db()
        with self._connect() as connection:
            # Values use SQL parameters; user text is never interpolated into
            # the statement itself.
            cursor = connection.execute(
                "INSERT INTO memories(key, value) VALUES (?, ?)", (key, value)
            )
            row = connection.execute(
                "SELECT * FROM memories WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def search_memory(self, query: str) -> List[Dict[str, object]]:
        self.init_db()
        terms = [term for term in query.lower().split() if len(term) > 2]
        with self._connect() as connection:
            if not terms:
                rows = connection.execute(
                    "SELECT * FROM memories ORDER BY id DESC LIMIT 20"
                ).fetchall()
            else:
                clauses = " OR ".join(
                    ["LOWER(key) LIKE ? OR LOWER(value) LIKE ?"] * len(terms)
                )
                params = []
                for term in terms:
                    params.extend([f"%{term}%", f"%{term}%"])
                rows = connection.execute(
                    f"SELECT * FROM memories WHERE {clauses} ORDER BY id DESC LIMIT 20",
                    params,
                ).fetchall()
        return [dict(row) for row in rows]

    def list_memories(self) -> List[Dict[str, object]]:
        self.init_db()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memories ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def clear_memories(self) -> int:
        self.init_db()
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            connection.execute("DELETE FROM memories")
        return int(count)


memory_store = MemoryStore()


def init_db() -> None:
    memory_store.init_db()


def save_memory(key: str, value: str) -> Dict[str, object]:
    return memory_store.save_memory(key, value)


def search_memory(query: str) -> List[Dict[str, object]]:
    return memory_store.search_memory(query)


def list_memories() -> List[Dict[str, object]]:
    return memory_store.list_memories()


def clear_memories() -> int:
    return memory_store.clear_memories()
