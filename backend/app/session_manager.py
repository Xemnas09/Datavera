import os
import time
import uuid
import shutil
import logging
import duckdb
from pathlib import Path
from typing import Dict, Optional, Tuple
from app.config import SESSIONS_DIR, SESSION_INACTIVITY_TIMEOUT_MINUTES

logger = logging.getLogger("datavera.session_manager")

class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db_path = SESSIONS_DIR / f"session_{session_id}.duckdb"
        self.created_at = time.time()
        self.last_activity = time.time()
        self.dataset_filename: Optional[str] = None
        self.table_name: str = "dataset"
        self.classifications: Dict[str, Any] = {}
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def touch(self):
        self.last_activity = time.time()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        self.touch()
        if self._conn is None:
            self._conn = duckdb.connect(database=str(self.db_path))
        return self._conn

    def close(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                logger.error(f"Error closing connection for session {self.session_id}: {e}")
            self._conn = None

        # Remove DB file and temporary sidecars
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception as e:
                logger.error(f"Error deleting file {self.db_path}: {e}")

        wal_path = Path(str(self.db_path) + ".wal")
        if wal_path.exists():
            try:
                wal_path.unlink()
            except Exception as e:
                logger.error(f"Error deleting WAL file {wal_path}: {e}")

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> Tuple[Session, bool]:
        self.cleanup_expired_sessions()

        created = False
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid.uuid4())
            session = Session(session_id)
            self.sessions[session_id] = session
            created = True
        else:
            session = self.sessions[session_id]
            session.touch()

        return session, created

    def get_session(self, session_id: str) -> Optional[Session]:
        self.cleanup_expired_sessions()
        session = self.sessions.get(session_id)
        if session:
            session.touch()
        return session

    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            session.close()

    def cleanup_expired_sessions(self):
        now = time.time()
        timeout_seconds = SESSION_INACTIVITY_TIMEOUT_MINUTES * 60
        expired_ids = [
            sid for sid, sess in self.sessions.items()
            if (now - sess.last_activity) > timeout_seconds
        ]
        for sid in expired_ids:
            logger.info(f"Cleaning up expired session {sid}")
            self.remove_session(sid)

# Global Session Manager Singleton
session_manager = SessionManager()
