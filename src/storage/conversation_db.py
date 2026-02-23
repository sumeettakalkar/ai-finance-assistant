"""SQLite-backed conversation storage.

Provides CRUD operations for conversations and messages. The database
is auto-created on first use with WAL mode for concurrent Streamlit sessions.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.storage.models import Conversation, Message

_DEFAULT_DB_PATH = Path("data/conversations.db")


class ConversationDB:
    """SQLite conversation store."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or _DEFAULT_DB_PATH)
        self._shared_conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        # For :memory: databases, reuse a single connection so schema persists
        if self._db_path == ":memory:":
            if self._shared_conn is None:
                self._shared_conn = sqlite3.connect(":memory:")
                self._shared_conn.row_factory = sqlite3.Row
                self._shared_conn.execute("PRAGMA foreign_keys=ON")
            return self._shared_conn
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _close(self, conn: sqlite3.Connection) -> None:
        """Close connection unless it's the shared in-memory one."""
        if conn is not self._shared_conn:
            conn.close()

    def _ensure_schema(self) -> None:
        # Ensure parent directory exists (skip for :memory:)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    tab TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    seq INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conv
                    ON messages(conversation_id, seq);
            """)
            conn.commit()
        finally:
            self._close(conn)

    # ------------------------------------------------------------------
    # Conversation CRUD
    # ------------------------------------------------------------------

    def create_conversation(self, tab: str, title: str = "") -> Conversation:
        """Create a new conversation. Title auto-generated if empty."""
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not title:
            title = "New Conversation"

        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO conversations (id, title, tab, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, tab, now, now),
            )
            conn.commit()
        finally:
            self._close(conn)

        return Conversation(
            id=conv_id, title=title, tab=tab,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def list_conversations(self, tab: Optional[str] = None, limit: int = 50) -> List[Conversation]:
        """List conversations, optionally filtered by tab, most recent first."""
        conn = self._connect()
        try:
            if tab:
                rows = conn.execute(
                    "SELECT * FROM conversations WHERE tab = ? ORDER BY updated_at DESC LIMIT ?",
                    (tab, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            return [
                Conversation(
                    id=r["id"], title=r["title"], tab=r["tab"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                )
                for r in rows
            ]
        finally:
            self._close(conn)

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get a conversation with all its messages."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,)
            ).fetchone()
            if not row:
                return None

            msg_rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY seq",
                (conv_id,),
            ).fetchall()

            messages = [
                Message(
                    id=m["id"],
                    conversation_id=m["conversation_id"],
                    role=m["role"],
                    content=m["content"],
                    sources=json.loads(m["sources"]) if m["sources"] else None,
                    metadata=json.loads(m["metadata"]) if m["metadata"] else None,
                    created_at=datetime.fromisoformat(m["created_at"]),
                    seq=m["seq"],
                )
                for m in msg_rows
            ]

            return Conversation(
                id=row["id"], title=row["title"], tab=row["tab"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                messages=messages,
            )
        finally:
            self._close(conn)

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation and all its messages."""
        conn = self._connect()
        try:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self._close(conn)

    def update_conversation_title(self, conv_id: str, title: str) -> None:
        """Update the title of a conversation."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id),
            )
            conn.commit()
        finally:
            self._close(conn)

    # ------------------------------------------------------------------
    # Message CRUD
    # ------------------------------------------------------------------

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Append a message to a conversation."""
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn = self._connect()
        try:
            # Get next sequence number
            row = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            seq = row["next_seq"]

            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, sources, metadata, created_at, seq) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    msg_id,
                    conversation_id,
                    role,
                    content,
                    json.dumps(sources) if sources else None,
                    json.dumps(metadata) if metadata else None,
                    now,
                    seq,
                ),
            )

            # Update conversation timestamp and title if first message
            if seq == 1 and role == "user":
                title = content[:60].strip()
                if len(content) > 60:
                    title += "..."
                conn.execute(
                    "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                    (title, now, conversation_id),
                )
            else:
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )

            conn.commit()
        finally:
            self._close(conn)

        return Message(
            id=msg_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            metadata=metadata,
            created_at=datetime.fromisoformat(now),
            seq=seq,
        )

    def get_recent_messages(
        self, conversation_id: str, limit: int = 10
    ) -> List[Message]:
        """Get the most recent messages from a conversation."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY seq DESC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()

            messages = [
                Message(
                    id=m["id"],
                    conversation_id=m["conversation_id"],
                    role=m["role"],
                    content=m["content"],
                    sources=json.loads(m["sources"]) if m["sources"] else None,
                    metadata=json.loads(m["metadata"]) if m["metadata"] else None,
                    created_at=datetime.fromisoformat(m["created_at"]),
                    seq=m["seq"],
                )
                for m in rows
            ]
            # Return in chronological order
            messages.reverse()
            return messages
        finally:
            self._close(conn)
