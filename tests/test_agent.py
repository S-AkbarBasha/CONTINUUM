import pytest
from agents.common.base_agent import BaseExecutionAgent
from agents.kali_agent.agent import executor as kali_executor
from agents.parrot_agent.agent import executor as parrot_executor

def test_agent_get_info():
    kali_info = kali_executor.get_info()
    assert kali_info["agent_id"] == "kali_primary"
    assert "Kali" in kali_info["os_name"]
    assert kali_info["status"] == "online"

    parrot_info = parrot_executor.get_info()
    assert parrot_info["agent_id"] == "parrot_backup"
    assert "Parrot" in parrot_info["os_name"]
    assert parrot_info["status"] == "online"

def test_execute_valid_c_program():
    code = """#include <stdio.h>
int main() {
    printf("Continuous OS Continuity\\n");
    return 0;
}
"""
    res = kali_executor.execute_job(
        job_id="test_job_1",
        source_code=code,
        compiler_flags=["-Wall", "-O2"]
    )
    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "Continuous OS Continuity" in res["stdout"]
    assert not res["env_error"]

def test_kali_incompatible_header_triggers_env_error():
    # Program with header that Kali config forbids
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("Test\\n");
    return 0;
}
"""
    res = kali_executor.execute_job(
        job_id="test_job_incompatible",
        source_code=code
    )
    assert res["success"] is False
    assert res["env_error"] is True
    assert "parrot_exclusive.h" in res["env_error_reason"]
    assert "No such file or directory" in res["compiler_output"] or "fatal error" in res["compiler_output"]

def test_parrot_accepts_and_executes_exclusive_header():
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("Success on Parrot OS\\n");
    return 0;
}
"""
    res = parrot_executor.execute_job(
        job_id="test_job_parrot_ok",
        source_code=code
    )
    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "Success on Parrot OS" in res["stdout"]

def test_syntax_error_not_env_error():
    code = """#include <stdio.h>
int main() {
    printf("Missing semicolon")
    return 0;
}
"""
    res = kali_executor.execute_job(
        job_id="test_job_syntax",
        source_code=code
    )
    assert res["success"] is False
    assert res["env_error"] is False
    assert "error:" in res["compiler_output"] or "expected" in res["compiler_output"]

def test_execution_timeout_detection():
    code = """#include <stdio.h>
int main() {
    while(1) {}
    return 0;
}
"""
    res = kali_executor.execute_job(
        job_id="test_job_timeout",
        source_code=code,
        timeout_seconds=0.5
    )
    assert res["success"] is False
    assert res["timed_out"] is True
    assert res["exit_code"] == -9
