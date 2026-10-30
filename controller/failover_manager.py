import os
import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import httpx

from backend.config import settings, PROGRAMS_DIR, LOGS_DIR
from backend.models import (
    create_job,
    get_job,
    update_job,
    add_timeline_event,
    record_migration,
    now_iso
)
from controller.failure_classifier import FailureClassifier, FailureCategory

logger = logging.getLogger("continuum.failover")

class FailoverManager:
    """
    Central orchestration controller. Manages:
    1. Job registration & source persistence
    2. Primary execution on Kali Linux
    3. Failure classification (Program vs Environment)
    4. User-approved or automatic failover to Parrot OS
    5. Detailed audit timeline and log archiving
    """

    def __init__(self, kali_url: Optional[str] = None, parrot_url: Optional[str] = None):
        self.kali_url = (kali_url or settings.kali_agent_url).rstrip("/")
        self.parrot_url = (parrot_url or settings.parrot_agent_url).rstrip("/")
        self._lock = threading.Lock()
        self._job_simulations: Dict[str, Dict[str, Any]] = {}

    def check_agent_health(self, base_url: str, timeout: float = 2.5) -> Dict[str, Any]:
        """Queries an agent's /health endpoint and measures latency."""
        start = time.time()
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.get(f"{base_url}/health")
                latency_ms = (time.time() - start) * 1000
                if res.status_code == 200:
                    data = res.json()
                    data["latency_ms"] = round(latency_ms, 2)
                    data["status"] = "online"
                    return data
                else:
                    return {
                        "status": "degraded",
                        "latency_ms": round(latency_ms, 2),
                        "error": f"HTTP {res.status_code}: {res.text}"
                    }
        except Exception as e:
            return {
                "status": "offline",
                "latency_ms": 0.0,
                "error": str(e)
            }

    def run_program(
        self,
        job_id: str,
        title: str,
        source_code: str,
        compiler_flags: Optional[List[str]] = None,
        stdin_data: str = "",
        timeout_seconds: float = 10.0,
        simulate_kali_env_failure: bool = False,
        simulate_parrot_offline: bool = False,
        simulate_failure_reason: Optional[str] = None,
        auto_migrate: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a program through the CONTINUUM pipeline.
        Single entry point for the user.
        """
        compiler_flags = compiler_flags or ["-Wall", "-O2"]
        
        # Save simulation settings for possible later user-approved migration
        self._job_simulations[job_id] = {
            "simulate_kali_env_failure": simulate_kali_env_failure,
            "simulate_parrot_offline": simulate_parrot_offline,
            "simulate_failure_reason": simulate_failure_reason
        }

        # Step 1: Save C source code to disk
        source_path = PROGRAMS_DIR / f"{job_id}.c"
        try:
            source_path.write_text(source_code, encoding="utf-8")
        except Exception as e:
            logger.error("Failed to write source code to disk: %s", e)

        # Step 2: Register Job in SQLite DB
        job = create_job(
            job_id=job_id,
            title=title,
            source_code=source_code,
            compiler_flags=compiler_flags,
            stdin_data=stdin_data,
            timeout_seconds=timeout_seconds,
            primary_target="Kali Linux"
        )
        add_timeline_event(
            job_id=job_id,
            stage="SUBMIT",
            status="info",
            message=f"Job {job_id} submitted. Saved source code to storage/programs/{job_id}.c"
        )

        # Step 3: Attempt execution on Primary Environment (Kali Linux)
        add_timeline_event(
            job_id=job_id,
            stage="KALI_DISPATCH",
            status="info",
            message=f"Connecting to Primary Environment: Kali Linux ({self.kali_url})..."
        )
        update_job(job_id, status="RUNNING_KALI", executed_on="Kali Linux")

        kali_result = self._dispatch_to_agent(
            base_url=self.kali_url,
            job_id=job_id,
            source_code=source_code,
            compiler_flags=compiler_flags,
            stdin_data=stdin_data,
            timeout_seconds=timeout_seconds,
            simulate_env_error=simulate_kali_env_failure,
            simulate_failure_reason=simulate_failure_reason
        )

        # Step 4: Evaluate Kali execution result
        if kali_result.get("agent_reachable", True) and kali_result.get("success", False):
            # SUCCESS on Kali Linux!
            update_job(
                job_id=job_id,
                status="SUCCESS_KALI",
                executed_on="Kali Linux",
                exit_code=kali_result.get("exit_code", 0),
                stdout=kali_result.get("stdout", ""),
                stderr=kali_result.get("stderr", ""),
                compiler_output=kali_result.get("compiler_output", ""),
                execution_time_ms=kali_result.get("execution_time_ms", 0.0),
                failure_type=FailureCategory.NONE.value,
                failure_reason=None,
                migrated=0,
                completed_at=now_iso()
            )
            add_timeline_event(
                job_id=job_id,
                stage="KALI_RESULT",
                status="success",
                message=f"Successfully compiled and executed on Kali Linux (exit code 0 in {kali_result.get('execution_time_ms', 0):.1f}ms)."
            )
            self._save_execution_log(job_id, "Kali Linux", kali_result)
            return get_job(job_id)

        # Step 5: Failure occurred - Run Failure Classifier
        classification = FailureClassifier.classify(
            exit_code=kali_result.get("exit_code"),
            stage=kali_result.get("stage", "compile"),
            stdout=kali_result.get("stdout", ""),
            stderr=kali_result.get("stderr", ""),
            compiler_output=kali_result.get("compiler_output", ""),
            agent_reachable=kali_result.get("agent_reachable", True),
            timed_out=kali_result.get("timed_out", False),
            env_error_flag=kali_result.get("env_error", False) or simulate_kali_env_failure,
            env_error_reason=kali_result.get("env_error_reason") or simulate_failure_reason
        )

        add_timeline_event(
            job_id=job_id,
            stage="CLASSIFICATION",
            status="warning" if classification.should_migrate else "error",
            message=f"Failure Analysis: {classification.category.value} [{classification.rule_matched}] - {classification.reason}"
        )

        # Step 6: Determine Migration Decision
        if not classification.should_migrate:
            # Normal program error (syntax, logic) or timeout. DO NOT MIGRATE.
            status = "TIMEOUT" if classification.category == FailureCategory.TIMEOUT else "FAILED_KALI_NORMAL"
            update_job(
                job_id=job_id,
                status=status,
                executed_on="Kali Linux",
                exit_code=kali_result.get("exit_code", 1),
                stdout=kali_result.get("stdout", ""),
                stderr=kali_result.get("stderr", ""),
                compiler_output=kali_result.get("compiler_output", ""),
                execution_time_ms=kali_result.get("execution_time_ms", 0.0),
                failure_type=classification.category.value,
                failure_reason=classification.reason,
                migrated=0,
                completed_at=now_iso()
            )
            add_timeline_event(
                job_id=job_id,
                stage="COMPLETED",
                status="error" if status != "TIMEOUT" else "warning",
                message=f"Execution halted without migration. Diagnosis: {classification.reason}"
            )
            self._save_execution_log(job_id, "Kali Linux (Failed - No Migration)", kali_result)
            return get_job(job_id)

        # Step 7: Environment Failure Detected
        if not auto_migrate:
            # STOP automatic migration and await user authorization!
            update_job(
                job_id=job_id,
                status="AWAITING_APPROVAL",
                executed_on="Kali Linux",
                exit_code=kali_result.get("exit_code", 1),
                stdout=kali_result.get("stdout", ""),
                stderr=kali_result.get("stderr", ""),
                compiler_output=kali_result.get("compiler_output", ""),
                execution_time_ms=kali_result.get("execution_time_ms", 0.0),
                failure_type=classification.category.value,
                failure_reason=classification.reason,
                migrated=0
            )
            add_timeline_event(
                job_id=job_id,
                stage="AWAITING_APPROVAL",
                status="warning",
                message=f"Kali Linux encountered an environment failure ({classification.reason}). Awaiting user authorization for failover to Parrot OS."
            )
            self._save_execution_log(job_id, "Kali Linux (Environment Failure - Awaiting Approval)", kali_result)
            return get_job(job_id)

        # Automatic Migration fallback if auto_migrate is explicitly True
        add_timeline_event(
            job_id=job_id,
            stage="MIGRATION_TRIGGER",
            status="warning",
            message=f"Environment failure confirmed in Kali. Initiating automatic failover to Backup Environment (Parrot OS)..."
        )
        update_job(
            job_id=job_id,
            status="MIGRATING_PARROT",
            failure_type=classification.category.value,
            failure_reason=classification.reason
        )
        return self._execute_parrot_migration(
            job_id=job_id,
            classification_reason=classification.reason,
            failure_type=classification.category.value,
            kali_error=kali_result.get("stderr") or kali_result.get("compiler_output") or "",
            simulate_parrot_offline=simulate_parrot_offline
        )

    def approve_migration(
        self,
        job_id: str,
        simulate_parrot_offline: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        User approved migration to Parrot OS.
        Thread-safe to prevent duplicate migration requests if clicked multiple times.
        """
        with self._lock:
            job = get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found.")

            # If already migrated or in-flight, safely return without re-dispatching
            if job["status"] in ("MIGRATING_PARROT", "RUNNING_PARROT", "SUCCESS_PARROT_MIGRATED", "FAILED_PARROT", "MIGRATION_FAILED"):
                logger.info(f"Duplicate approval for job {job_id} ignored; status is {job['status']}")
                return job

            if job["status"] != "AWAITING_APPROVAL":
                raise ValueError(f"Job '{job_id}' is not awaiting approval (status: {job['status']})")

            # Mark state to prevent race conditions
            update_job(job_id, status="MIGRATING_PARROT")
            add_timeline_event(
                job_id=job_id,
                stage="USER_DECISION",
                status="info",
                message="User approved failover: Initiating migration to Parrot OS."
            )

        sim_flags = self._job_simulations.get(job_id, {})
        is_offline_sim = (
            simulate_parrot_offline
            if simulate_parrot_offline is not None
            else sim_flags.get("simulate_parrot_offline", False)
        )

        return self._execute_parrot_migration(
            job_id=job_id,
            classification_reason=job.get("failure_reason") or "Environment issue on Kali Linux",
            failure_type=job.get("failure_type") or "ENVIRONMENT_FAILURE",
            kali_error=job.get("stderr") or job.get("compiler_output") or "",
            simulate_parrot_offline=is_offline_sim
        )

    def decline_migration(self, job_id: str) -> Dict[str, Any]:
        """
        User declined migration. Stays on Kali Linux and marks migration as declined.
        Does not contact Parrot OS.
        """
        with self._lock:
            job = get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found.")

            if job["status"] == "MIGRATION_DECLINED":
                return job

            if job["status"] != "AWAITING_APPROVAL":
                raise ValueError(f"Job '{job_id}' is not awaiting approval (status: {job['status']})")

            update_job(
                job_id=job_id,
                status="MIGRATION_DECLINED",
                executed_on="Kali Linux",
                migrated=0,
                completed_at=now_iso()
            )
            add_timeline_event(
                job_id=job_id,
                stage="USER_DECISION",
                status="warning",
                message="User declined migration to Parrot OS. Execution halted on Kali Linux."
            )
            add_timeline_event(
                job_id=job_id,
                stage="COMPLETED",
                status="error",
                message=f"Execution finalized on Kali Linux (Migration declined by user). Original failure: {job.get('failure_reason')}"
            )
            record_migration(
                job_id=job_id,
                from_env="Kali Linux",
                to_env="Parrot OS",
                failure_type=job.get("failure_type") or "ENVIRONMENT_FAILURE",
                reason=f"Migration declined by user. Original failure: {job.get('failure_reason')}",
                success=False,
                details=json.dumps({"user_decision": "declined", "status": "declined"})
            )
            return get_job(job_id)

    def resolve_migration(
        self,
        job_id: str,
        approved: bool,
        simulate_parrot_offline: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Resolves user migration decision (approve or decline)."""
        if approved:
            return self.approve_migration(job_id, simulate_parrot_offline=simulate_parrot_offline)
        else:
            return self.decline_migration(job_id)

    def _execute_parrot_migration(
        self,
        job_id: str,
        classification_reason: str,
        failure_type: str,
        kali_error: str,
        simulate_parrot_offline: bool = False
    ) -> Dict[str, Any]:
        """Executes failover to Parrot OS."""
        job = get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found.")

        # Check Parrot OS Availability
        parrot_health = self.check_agent_health(self.parrot_url)
        is_parrot_available = (parrot_health.get("status") == "online") and not simulate_parrot_offline

        if not is_parrot_available:
            fail_reason = (
                "Backup environment (Parrot OS) is offline or unreachable." 
                if not simulate_parrot_offline 
                else "Simulated Parrot OS unavailability during failover."
            )
            record_migration(
                job_id=job_id,
                from_env="Kali Linux",
                to_env="Parrot OS",
                failure_type=failure_type,
                reason=fail_reason,
                success=False,
                details=json.dumps({
                    "kali_failure": classification_reason,
                    "parrot_health": parrot_health
                })
            )
            update_job(
                job_id=job_id,
                status="MIGRATION_FAILED",
                executed_on="Kali Linux (Migration Failed)",
                exit_code=1,
                failure_type=failure_type,
                failure_reason=f"{classification_reason} | Failover aborted: {fail_reason}",
                migrated=0,
                completed_at=now_iso()
            )
            add_timeline_event(
                job_id=job_id,
                stage="PARROT_RESULT",
                status="error",
                message=f"Migration failed: {fail_reason}"
            )
            return get_job(job_id)

        # Step 8: Transfer Program to Parrot OS & Restart Execution
        add_timeline_event(
            job_id=job_id,
            stage="PARROT_DISPATCH",
            status="info",
            message=f"Restoring source code, arguments, and stdin on Parrot OS ({self.parrot_url}). Starting execution..."
        )
        update_job(job_id, status="RUNNING_PARROT", executed_on="Parrot OS")

        parrot_result = self._dispatch_to_agent(
            base_url=self.parrot_url,
            job_id=job_id,
            source_code=job["source_code"],
            compiler_flags=job["compiler_flags"],
            stdin_data=job["stdin_data"],
            timeout_seconds=job["timeout_seconds"],
            simulate_env_error=False
        )

        # Record migration event
        is_parrot_success = parrot_result.get("success", False)
        record_migration(
            job_id=job_id,
            from_env="Kali Linux",
            to_env="Parrot OS",
            failure_type=failure_type,
            reason=classification_reason,
            success=is_parrot_success,
            details=json.dumps({
                "kali_error": kali_error,
                "parrot_status": "success" if is_parrot_success else "failed",
                "stdin_preserved": True,
                "stdin_chars": len(job.get("stdin_data") or "")
            })
        )

        # Update final job state
        final_status = "SUCCESS_PARROT_MIGRATED" if is_parrot_success else "FAILED_PARROT"
        update_job(
            job_id=job_id,
            status=final_status,
            executed_on="Parrot OS",
            exit_code=parrot_result.get("exit_code", 0 if is_parrot_success else 1),
            stdout=parrot_result.get("stdout", ""),
            stderr=parrot_result.get("stderr", ""),
            compiler_output=parrot_result.get("compiler_output", ""),
            execution_time_ms=parrot_result.get("execution_time_ms", 0.0),
            failure_type=failure_type if not is_parrot_success else "NONE",
            failure_reason=classification_reason,
            migrated=1,
            completed_at=now_iso()
        )

        add_timeline_event(
            job_id=job_id,
            stage="PARROT_RESULT",
            status="success" if is_parrot_success else "error",
            message=f"Parrot OS execution completed with exit code {parrot_result.get('exit_code', 0)}."
        )
        self._save_execution_log(job_id, "Parrot OS (Recovered via Failover)", parrot_result)
        return get_job(job_id)

    def _dispatch_to_agent(
        self,
        base_url: str,
        job_id: str,
        source_code: str,
        compiler_flags: List[str],
        stdin_data: str,
        timeout_seconds: float,
        simulate_env_error: bool = False,
        simulate_failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sends HTTP request to execution agent endpoint."""
        url = f"{base_url}/execute"
        payload = {
            "job_id": job_id,
            "source_code": source_code,
            "compiler_flags": compiler_flags,
            "stdin": stdin_data,
            "stdin_data": stdin_data,
            "timeout_seconds": timeout_seconds,
            "simulate_env_error": simulate_env_error,
            "simulate_failure_reason": simulate_failure_reason
        }

        # Allow extra time for compile + run
        req_timeout = timeout_seconds + settings.compile_timeout + 5.0
        try:
            with httpx.Client(timeout=req_timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    data["agent_reachable"] = True
                    return data
                elif res.status_code == 503:
                    # Service Unavailable / simulated offline
                    return {
                        "success": False,
                        "stage": "dispatch",
                        "exit_code": 1,
                        "stdout": "",
                        "stderr": f"Agent returned HTTP 503: {res.text}",
                        "compiler_output": "",
                        "agent_reachable": False,
                        "timed_out": False,
                        "execution_time_ms": 0.0,
                        "env_error": True,
                        "env_error_reason": f"Agent unavailable (HTTP 503) at {base_url}"
                    }
                else:
                    return {
                        "success": False,
                        "stage": "dispatch",
                        "exit_code": res.status_code,
                        "stdout": "",
                        "stderr": f"Agent HTTP error {res.status_code}: {res.text}",
                        "compiler_output": "",
                        "agent_reachable": True,
                        "timed_out": False,
                        "execution_time_ms": 0.0,
                        "env_error": True,
                        "env_error_reason": f"Unexpected HTTP status {res.status_code} from {base_url}"
                    }
        except httpx.ConnectError as e:
            return {
                "success": False,
                "stage": "dispatch",
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Connection to {base_url} refused. Agent appears offline.",
                "compiler_output": "",
                "agent_reachable": False,
                "timed_out": False,
                "execution_time_ms": 0.0,
                "env_error": True,
                "env_error_reason": f"Cannot connect to agent at {base_url}: {e}"
            }
        except httpx.TimeoutException as e:
            return {
                "success": False,
                "stage": "dispatch",
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Request to agent at {base_url} timed out.",
                "compiler_output": "",
                "agent_reachable": False,
                "timed_out": True,
                "execution_time_ms": timeout_seconds * 1000,
                "env_error": True,
                "env_error_reason": f"Agent connection timed out at {base_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "stage": "dispatch",
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Unexpected error contacting agent: {e}",
                "compiler_output": "",
                "agent_reachable": False,
                "timed_out": False,
                "execution_time_ms": 0.0,
                "env_error": True,
                "env_error_reason": str(e)
            }

    def _save_execution_log(self, job_id: str, environment_label: str, result: Dict[str, Any]):
        """Saves combined execution log file."""
        log_file = LOGS_DIR / f"{job_id}.log"
        content = [
            f"=== CONTINUUM EXECUTION AUDIT LOG ===",
            f"Job ID: {job_id}",
            f"Timestamp: {now_iso()}",
            f"Executed On: {environment_label}",
            f"Success: {result.get('success')}",
            f"Exit Code: {result.get('exit_code')}",
            f"Execution Time: {result.get('execution_time_ms', 0):.2f} ms",
            f"--- COMPILER OUTPUT ---",
            result.get("compiler_output", "").strip(),
            f"--- STDOUT ---",
            result.get("stdout", "").strip(),
            f"--- STDERR ---",
            result.get("stderr", "").strip(),
            f"====================================="
        ]
        try:
            log_file.write_text("\n".join(content), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to write log file %s: %s", log_file, e)

# Singleton controller instance
failover_controller = FailoverManager()
