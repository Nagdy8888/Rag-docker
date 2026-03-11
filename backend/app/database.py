"""Database connection and helpers using DATABASE_URI (Supabase Postgres)."""

from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine

from app.config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the SQLAlchemy engine (creates on first call)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.database_uri:
            raise ValueError("DATABASE_URI is not set in environment")
        _engine = create_engine(
            settings.database_uri,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


@contextmanager
def get_connection():
    """Context manager yielding a connection. Use for all DB operations."""
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _row_to_dict(row) -> dict:
    """Convert a result row to a dict with string keys."""
    return dict(row._mapping) if hasattr(row, "_mapping") else dict(row)


def list_sessions():
    """Return all chat_sessions ordered by updated_at desc."""
    with get_connection() as conn:
        r = conn.execute(
            text("SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC")
        )
        return [_row_to_dict(row) for row in r]


def get_session(session_id: UUID):
    """Return one chat_session by id or None."""
    with get_connection() as conn:
        r = conn.execute(
            text("SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = :id"),
            {"id": str(session_id)},
        )
        row = r.fetchone()
        return _row_to_dict(row) if row else None


def get_messages(session_id: UUID):
    """Return all chat_messages for a session ordered by created_at."""
    with get_connection() as conn:
        r = conn.execute(
            text(
                "SELECT id, session_id, role, content, created_at FROM chat_messages "
                "WHERE session_id = :session_id ORDER BY created_at"
            ),
            {"session_id": str(session_id)},
        )
        return [_row_to_dict(row) for row in r]


def create_session(title: str = "New Chat"):
    """Insert a new chat_session and return it."""
    with get_connection() as conn:
        r = conn.execute(
            text(
                "INSERT INTO chat_sessions (title) VALUES (:title) "
                "RETURNING id, title, created_at, updated_at"
            ),
            {"title": title},
        )
        row = r.fetchone()
        return _row_to_dict(row)


def delete_session(session_id: UUID):
    """Delete a chat_session and its messages (CASCADE handles messages)."""
    with get_connection() as conn:
        conn.execute(text("DELETE FROM chat_messages WHERE session_id = :id"), {"id": str(session_id)})
        conn.execute(text("DELETE FROM chat_sessions WHERE id = :id"), {"id": str(session_id)})


def insert_message(session_id: UUID, role: str, content: str):
    """Insert a chat_message. Trigger will update session.updated_at."""
    with get_connection() as conn:
        conn.execute(
            text(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (:session_id, :role, :content)"
            ),
            {"session_id": str(session_id), "role": role, "content": content},
        )


def update_session_title(session_id: UUID, title: str):
    """Update a session's title."""
    with get_connection() as conn:
        conn.execute(
            text("UPDATE chat_sessions SET title = :title WHERE id = :id"),
            {"id": str(session_id), "title": title},
        )


def list_files():
    """Return all files (processed documents) ordered by created_at desc."""
    with get_connection() as conn:
        try:
            r = conn.execute(
                text(
                    "SELECT id, filename, file_type, file_size, chunk_count, status, error_message, created_at "
                    "FROM files ORDER BY created_at DESC"
                )
            )
        except Exception:
            r = conn.execute(
                text(
                    "SELECT id, filename, file_type, file_size, chunk_count, status, created_at "
                    "FROM files ORDER BY created_at DESC"
                )
            )
        rows = [_row_to_dict(row) for row in r]
        for row in rows:
            if "error_message" not in row:
                row["error_message"] = None
        return rows
