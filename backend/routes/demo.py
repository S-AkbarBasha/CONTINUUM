from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.routes.jobs import submit_job
from backend.schemas import JobCreateRequest, JobResponse

router = APIRouter(prefix="/api/demo", tags=["Demo Test Presets"])

# Test Case 1: Valid C program in Kali
TEST_1_CODE = """#include <stdio.h>

int main() {
    printf("========================================\\n");
    printf("   CONTINUUM System Execution Demo      \\n");
    printf("========================================\\n");
    printf("Hello from C program!\\n");
    printf("Primary execution target: Kali Linux VM\\n");
    printf("Computation check: 42 * 10 = %d\\n", 42 * 10);
    printf("Execution status: SUCCESS (Exit 0)\\n");
    return 0;
}
"""

# Test Case 2: Program requiring dependency available on Parrot but missing on Kali
TEST_2_CODE = """#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("============================================\\n");
    printf("   CONTINUUM Failover Verification Demo     \\n");
    printf("============================================\\n");
    printf("Header 'parrot_exclusive.h' successfully loaded!\\n");
    printf("Running on Backup Environment: Parrot OS\\n");
    printf("Cross-OS continuity succeeded without manual intervention!\\n");
    return 0;
}
"""

# Test Case 3: C syntax error
TEST_3_CODE = """#include <stdio.h>

int main() {
    printf("Starting syntax test...\\n")  // MISSING SEMICOLON HERE!
    int x = undeclared_variable + 10;
    return 0;
}
"""

# Test Case 4: Environment failure when Parrot is simulated offline
TEST_4_CODE = """#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("This program will attempt migration to Parrot OS.\\n");
    return 0;
}
"""

# Test Case 5: Infinite loop / timeout
TEST_5_CODE = """#include <stdio.h>
#include <unistd.h>

int main() {
    printf("Program entering long execution loop...\\n");
    while (1) {
        // Simulates hang or infinite computation
    }
    return 0;
}
"""

@router.get("/presets")
def get_presets():
    """Returns the 5 test presets with metadata and descriptions."""
    return {
        "test_1": {
            "title": "Test 1: Normal Execution in Kali",
            "description": "Valid C program executes in primary environment (Kali Linux). Expected: Exit 0, No migration.",
            "source_code": TEST_1_CODE,
            "compiler_flags": ["-Wall", "-O2"],
            "timeout_seconds": 10.0,
            "simulate_kali_env_failure": False,
            "simulate_parrot_offline": False
        },
        "test_2": {
            "title": "Test 2: User-Approved Kali -> Parrot Failover",
            "description": "Program requests environment feature missing in Kali. Expected: Classified as Environment Failure, halts for user approval, and executes on Parrot OS upon approval.",
            "source_code": TEST_2_CODE,
            "compiler_flags": ["-Wall", "-O2"],
            "timeout_seconds": 10.0,
            "simulate_kali_env_failure": False,
            "simulate_parrot_offline": False
        },
        "test_3": {
            "title": "Test 3: C Syntax Error (No Migration)",
            "description": "Program contains syntax defect (missing semicolon & undeclared var). Expected: Classified as Program Error, compiler diagnostics returned, NO migration.",
            "source_code": TEST_3_CODE,
            "compiler_flags": ["-Wall", "-O2"],
            "timeout_seconds": 10.0,
            "simulate_kali_env_failure": False,
            "simulate_parrot_offline": False
        },
        "test_4": {
            "title": "Test 4: Backup Environment Unavailable",
            "description": "Kali environment failure triggers failover, but Parrot OS is unavailable. Expected: Clear migration failure message.",
            "source_code": TEST_4_CODE,
            "compiler_flags": ["-Wall", "-O2"],
            "timeout_seconds": 10.0,
            "simulate_kali_env_failure": True,
            "simulate_parrot_offline": True,
            "simulate_failure_reason": "Kali kernel driver missing and Parrot OS VM is offline."
        },
        "test_5": {
            "title": "Test 5: Program Timeout Protection",
            "description": "Program enters infinite loop. Expected: Execution timeout triggered, process terminated cleanly, timeout recorded.",
            "source_code": TEST_5_CODE,
            "compiler_flags": ["-Wall", "-O2"],
            "timeout_seconds": 3.0,
            "simulate_kali_env_failure": False,
            "simulate_parrot_offline": False
        }
    }

@router.post("/run-test/{test_id}", response_model=JobResponse)
def trigger_test_preset(test_id: str):
    """Triggers one of the 5 standard test cases directly."""
    presets = get_presets()
    if test_id not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{test_id}' not found. Valid: {list(presets.keys())}")

    p = presets[test_id]
    req = JobCreateRequest(
        title=p["title"],
        source_code=p["source_code"],
        compiler_flags=p["compiler_flags"],
        timeout_seconds=p["timeout_seconds"],
        simulate_kali_env_failure=p.get("simulate_kali_env_failure", False),
        simulate_parrot_offline=p.get("simulate_parrot_offline", False),
        simulate_failure_reason=p.get("simulate_failure_reason")
    )
    return submit_job(req)
