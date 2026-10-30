import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.database import get_db

logger = logging.getLogger("continuum.models")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_job(
    job_id: str,
    title: str,
    source_code: str,
    compiler_flags: List[str],
    stdin_data: str = "",
    timeout_seconds: float = 10.0,
    primary_target: str = "Kali Linux"
) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        created_at = now_iso()
        flags_json = json.dumps(compiler_flags)
        cursor.execute("DELETE FROM timeline_events WHERE job_id = ?", (job_id,))
        cursor.execute("DELETE FROM migrations WHERE job_id = ?", (job_id,))
        cursor.execute("""
        INSERT OR REPLACE INTO jobs (
            id, title, source_code, compiler_flags, stdin_data,
            timeout_seconds, status, primary_target, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, title, source_code, flags_json, stdin_data,
            timeout_seconds, "PENDING", primary_target, created_at
        ))
    return get_job(job_id)

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            return None
        
        # Parse compiler_flags JSON
        try:
            job["compiler_flags"] = json.loads(job.get("compiler_flags") or "[]")
        except Exception:
            job["compiler_flags"] = []
        
        job["migrated"] = bool(job.get("migrated", 0))
        job["stdin"] = job.get("stdin_data") or ""
        job["timeline"] = get_timeline_events(job_id)
        job["migrations"] = get_migrations(job_id)
        return job

def update_job(job_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    if not kwargs:
        return get_job(job_id)
    
    # Process json or boolean conversions
    if "compiler_flags" in kwargs and isinstance(kwargs["compiler_flags"], list):
        kwargs["compiler_flags"] = json.dumps(kwargs["compiler_flags"])
    if "migrated" in kwargs:
        kwargs["migrated"] = 1 if kwargs["migrated"] else 0
        
    set_clauses = [f"{k} = ?" for k in kwargs.keys()]
    values = list(kwargs.values())
    values.append(job_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?", values)
    
    return get_job(job_id)

def list_jobs(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (limit, offset))
        jobs = cursor.fetchall()
        for j in jobs:
            try:
                j["compiler_flags"] = json.loads(j.get("compiler_flags") or "[]")
            except Exception:
                j["compiler_flags"] = []
            j["migrated"] = bool(j.get("migrated", 0))
            j["stdin"] = j.get("stdin_data") or ""
            # Don't fetch full timeline for list to keep it fast
            j["timeline"] = []
            j["migrations"] = []
        return jobs

def add_timeline_event(
    job_id: str,
    stage: str,
    status: str,
    message: str,
    details: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO timeline_events (job_id, timestamp, stage, status, message, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (job_id, now_iso(), stage, status, message, details))

def get_timeline_events(job_id: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT timestamp, stage, status, message, details
        FROM timeline_events
        WHERE job_id = ?
        ORDER BY id ASC
        """, (job_id,))
        return cursor.fetchall()

def record_migration(
    job_id: str,
    from_env: str,
    to_env: str,
    failure_type: str,
    reason: str,
    success: bool,
    details: Optional[str] = None
) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        migrated_at = now_iso()
        cursor.execute("""
        INSERT INTO migrations (
            job_id, from_env, to_env, failure_type, reason, migrated_at, success, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, from_env, to_env, failure_type, reason, migrated_at,
            1 if success else 0, details
        ))
        row_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM migrations WHERE id = ?", (row_id,))
        rec = cursor.fetchone()
        rec["success"] = bool(rec["success"])
        return rec

def get_migrations(job_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if job_id:
            cursor.execute("""
            SELECT * FROM migrations WHERE job_id = ? ORDER BY id DESC
            """, (job_id,))
        else:
            cursor.execute("""
            SELECT * FROM migrations ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        for r in rows:
            r["success"] = bool(r.get("success", 0))
        return rows

def upsert_agent_health(
    agent_id: str,
    agent_name: str,
    base_url: str,
    status: str,
    os_info: Optional[str] = None,
    compiler_info: Optional[str] = None,
    latency_ms: float = 0.0,
    details: Optional[Dict[str, Any]] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        details_json = json.dumps(details or {})
        cursor.execute("""
        INSERT INTO agent_health (
            agent_id, agent_name, base_url, status, last_checked,
            os_info, compiler_info, latency_ms, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(agent_id) DO UPDATE SET
            agent_name = excluded.agent_name,
            base_url = excluded.base_url,
            status = excluded.status,
            last_checked = excluded.last_checked,
            os_info = excluded.os_info,
            compiler_info = excluded.compiler_info,
            latency_ms = excluded.latency_ms,
            details = excluded.details
        """, (
            agent_id, agent_name, base_url, status, now_iso(),
            os_info, compiler_info, latency_ms, details_json
        ))

def get_all_agent_health() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_health ORDER BY agent_name ASC")
        rows = cursor.fetchall()
        for r in rows:
            try:
                r["details"] = json.loads(r.get("details") or "{}")
            except Exception:
                r["details"] = {}
        return rows
