import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from backend.schemas import JobCreateRequest, JobResponse, MigrationRecordSchema, MigrationDecisionRequest
from backend.models import get_job, list_jobs, get_migrations
from backend.config import PROGRAMS_DIR, LOGS_DIR
from controller.failover_manager import failover_controller

router = APIRouter(prefix="/api", tags=["Jobs"])

def generate_job_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    rand_suffix = uuid.uuid4().hex[:6]
    return f"job_{timestamp}_{rand_suffix}"

@router.post("/jobs/run", response_model=JobResponse)
def submit_job(req: JobCreateRequest):
    """
    Submits a C program to the CONTINUUM system.
    Executes in Kali Linux. If eligible environment failure occurs,
    pauses for user approval unless auto_migrate is explicitly requested.
    """
    job_id = generate_job_id()
    stdin_val = req.stdin if req.stdin is not None else (req.stdin_data or "")
    auto_migrate_val = req.auto_migrate if req.auto_migrate is not None else False
    result = failover_controller.run_program(
        job_id=job_id,
        title=req.title or "C Program",
        source_code=req.source_code,
        compiler_flags=req.compiler_flags,
        stdin_data=stdin_val,
        timeout_seconds=req.timeout_seconds or 10.0,
        simulate_kali_env_failure=req.simulate_kali_env_failure or False,
        simulate_parrot_offline=req.simulate_parrot_offline or False,
        simulate_failure_reason=req.simulate_failure_reason,
        auto_migrate=auto_migrate_val
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create and execute job.")
    return result

@router.post("/jobs/{job_id}/decision", response_model=JobResponse)
def handle_migration_decision(job_id: str, req: MigrationDecisionRequest):
    """
    User-approved failover decision:
    - approved=True -> Transfer and execute on Parrot OS.
    - approved=False -> Stay on Kali Linux and mark migration as declined.
    """
    try:
        result = failover_controller.resolve_migration(
            job_id=job_id,
            approved=req.approved,
            simulate_parrot_offline=req.simulate_parrot_offline
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/approve", response_model=JobResponse)
def approve_job_migration(job_id: str):
    """Approves migration to Parrot OS."""
    try:
        result = failover_controller.approve_migration(job_id=job_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/decline", response_model=JobResponse)
def decline_job_migration(job_id: str):
    """Declines migration and retains original Kali execution result."""
    try:
        result = failover_controller.decline_migration(job_id=job_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=List[JobResponse])
def get_jobs_list(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Lists past execution jobs."""
    jobs = list_jobs(limit=limit, offset=offset)
    return jobs

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: str):
    """Retrieves full details, timeline, and forensics for a single job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job

@router.get("/jobs/{job_id}/source")
def get_job_source_code(job_id: str):
    """Returns saved C source file from storage/programs/."""
    file_path = PROGRAMS_DIR / f"{job_id}.c"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Source file not found on disk.")
    return {"job_id": job_id, "source_code": file_path.read_text(encoding="utf-8")}

@router.get("/jobs/{job_id}/log")
def get_job_log_file(job_id: str):
    """Returns saved execution log file from storage/logs/."""
    file_path = LOGS_DIR / f"{job_id}.log"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found on disk.")
    return {"job_id": job_id, "log_content": file_path.read_text(encoding="utf-8")}

@router.get("/migrations", response_model=List[MigrationRecordSchema])
def get_all_migrations(limit: int = Query(50, ge=1, le=200)):
    """Returns migration history audit logs."""
    return get_migrations(limit=limit)
