from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum

class FailureCategory(str, Enum):
    NONE = "NONE"
    PROGRAM_ERROR = "PROGRAM_ERROR"              # Syntax, normal compile error, runtime logic error
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"  # Dependency missing, agent offline, unexecutable
    TIMEOUT = "TIMEOUT"                          # Execution timeout
    UNREACHABLE = "UNREACHABLE"                  # Agent unreachable over network

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING_KALI = "RUNNING_KALI"
    SUCCESS_KALI = "SUCCESS_KALI"
    FAILED_KALI_NORMAL = "FAILED_KALI_NORMAL"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    MIGRATING_PARROT = "MIGRATING_PARROT"
    RUNNING_PARROT = "RUNNING_PARROT"
    SUCCESS_PARROT_MIGRATED = "SUCCESS_PARROT_MIGRATED"
    FAILED_PARROT = "FAILED_PARROT"
    MIGRATION_FAILED = "MIGRATION_FAILED"
    MIGRATION_DECLINED = "MIGRATION_DECLINED"
    TIMEOUT = "TIMEOUT"

class JobCreateRequest(BaseModel):
    title: Optional[str] = "C Program"
    source_code: str = Field(..., description="C source code to execute")
    compiler_flags: List[str] = Field(default_factory=lambda: ["-Wall", "-O2"])
    stdin: Optional[str] = None
    stdin_data: Optional[str] = ""
    timeout_seconds: Optional[float] = 10.0
    auto_migrate: Optional[bool] = False
    # For testing/demo trigger:
    simulate_kali_env_failure: Optional[bool] = False
    simulate_parrot_offline: Optional[bool] = False
    simulate_failure_reason: Optional[str] = None

class MigrationDecisionRequest(BaseModel):
    approved: bool = Field(True, description="True to migrate to Parrot OS, False to stay on Kali Linux")
    simulate_parrot_offline: Optional[bool] = False

class TimelineEventSchema(BaseModel):
    timestamp: str
    stage: str
    status: str
    message: str
    details: Optional[str] = None

class MigrationRecordSchema(BaseModel):
    id: Optional[int] = None
    job_id: str
    from_env: str
    to_env: str
    failure_type: str
    reason: str
    migrated_at: str
    success: bool
    details: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    title: Optional[str]
    source_code: str
    compiler_flags: List[str]
    stdin: Optional[str] = None
    stdin_data: Optional[str] = ""
    timeout_seconds: float
    status: str
    primary_target: str
    executed_on: Optional[str]
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    compiler_output: Optional[str]
    execution_time_ms: float
    failure_type: str
    failure_reason: Optional[str]
    migrated: bool
    created_at: str
    completed_at: Optional[str]
    timeline: List[TimelineEventSchema] = []
    migrations: List[MigrationRecordSchema] = []

class AgentHealthResponse(BaseModel):
    agent_id: str
    agent_name: str
    base_url: str
    status: str                  # "online" | "offline" | "degraded"
    last_checked: str
    os_info: Optional[str] = None
    compiler_info: Optional[str] = None
    latency_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None

class AgentConfigUpdate(BaseModel):
    kali_agent_url: Optional[str] = None
    parrot_agent_url: Optional[str] = None
