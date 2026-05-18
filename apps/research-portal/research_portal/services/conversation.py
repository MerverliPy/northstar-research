"""SQLite-based conversation history storage."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    project_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL DEFAULT '',
    tool_results TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
"""


class ConversationStore:
    """Manages conversation and message persistence in SQLite."""

    def __init__(self, db_path: str = "~/.cache/northstar/conversations.db"):
        self._db_path = Path(os.path.expanduser(db_path))
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_conversation(self, title: str = "New Conversation", project_id: str | None = None) -> dict:
        import uuid
        conv_id = str(uuid.uuid4())
        now = self._now()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO conversations (id, title, project_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, title, project_id, now, now),
        )
        conn.commit()
        return {
            "id": conv_id,
            "title": title,
            "project_id": project_id,
            "created_at": now,
            "updated_at": now,
        }

    def list_conversations(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, conv_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if row is None:
            return None
        conv = dict(row)
        msgs = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
        conv["messages"] = []
        for msg in msgs:
            m = dict(msg)
            if m.get("tool_results"):
                try:
                    m["tool_results"] = json.loads(m["tool_results"])
                except (json.JSONDecodeError, TypeError):
                    m["tool_results"] = None
            conv["messages"].append(m)
        return conv

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_results: list | None = None,
    ) -> dict:
        import uuid
        msg_id = str(uuid.uuid4())
        now = self._now()
        conn = self._get_conn()
        tool_json = json.dumps(tool_results) if tool_results else None
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, tool_results, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, tool_json, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "tool_results": tool_results,
            "created_at": now,
        }

    def delete_conversation(self, conv_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        return cursor.rowcount > 0
