import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Any, Dict, List, Optional
from backend.config import DB_PATH

logger = logging.getLogger("continuum.database")

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = dict_factory
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def init_db():
    """Initializes SQLite tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Jobs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            source_code TEXT NOT NULL,
            compiler_flags TEXT DEFAULT '[]',
            stdin_data TEXT DEFAULT '',
            timeout_seconds REAL DEFAULT 10.0,
            status TEXT NOT NULL,
            primary_target TEXT DEFAULT 'Kali Linux',
            executed_on TEXT,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            compiler_output TEXT,
            execution_time_ms REAL DEFAULT 0.0,
            failure_type TEXT DEFAULT 'NONE',
            failure_reason TEXT,
            migrated INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
        """)
        
        # Migrations history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            from_env TEXT NOT NULL,
            to_env TEXT NOT NULL,
            failure_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            migrated_at TEXT NOT NULL,
            success INTEGER NOT NULL,
            details TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """)
        
        # Timeline events table for live audit trail
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """)
        
        # Agent status / health cache
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_health (
            agent_id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            status TEXT NOT NULL,
            last_checked TEXT NOT NULL,
            os_info TEXT,
            compiler_info TEXT,
            latency_ms REAL DEFAULT 0.0,
            details TEXT
        )
        """)
        
        conn.commit()
    logger.info("SQLite database initialized successfully at %s", DB_PATH)

if __name__ == "__main__":
    init_db()
