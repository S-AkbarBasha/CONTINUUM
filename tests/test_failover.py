import pytest
from unittest.mock import patch, MagicMock
from backend.database import init_db
from backend.models import get_job, get_migrations
from controller.failover_manager import FailoverManager
from agents.kali_agent.agent import executor as kali_executor
from agents.parrot_agent.agent import executor as parrot_executor

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

@pytest.fixture
def mock_controller():
    """
    Creates a FailoverManager instance that delegates network requests directly
    to the in-process Kali and Parrot execution agents for deterministic testing.
    """
    controller = FailoverManager(kali_url="http://mock-kali:8001", parrot_url="http://mock-parrot:8002")
    return controller

def simulated_dispatch(base_url, job_id, source_code, compiler_flags, stdin_data, timeout_seconds, simulate_env_error=False, simulate_failure_reason=None):
    """Directly dispatches to the corresponding agent's executor."""
    if "kali" in base_url:
        res = kali_executor.execute_job(
            job_id=job_id,
            source_code=source_code,
            compiler_flags=compiler_flags,
            stdin_data=stdin_data,
            timeout_seconds=timeout_seconds,
            simulate_env_error=simulate_env_error,
            simulate_failure_reason=simulate_failure_reason
        )
        res["agent_reachable"] = True
        return res
    elif "parrot" in base_url:
        res = parrot_executor.execute_job(
            job_id=job_id,
            source_code=source_code,
            compiler_flags=compiler_flags,
            stdin_data=stdin_data,
            timeout_seconds=timeout_seconds,
            simulate_env_error=simulate_env_error,
            simulate_failure_reason=simulate_failure_reason
        )
        res["agent_reachable"] = True
        return res
    return {"agent_reachable": False, "success": False, "exit_code": 1}

# TEST 1: Valid C program runs successfully in Kali. (No migration)
def test_scenario_1_valid_program_in_kali(mock_controller):
    code = """#include <stdio.h>
int main() {
    printf("Test 1: Hello from Kali Linux!\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_case_1",
            title="Test 1",
            source_code=code,
            compiler_flags=["-Wall", "-O2"]
        )

        assert res["status"] == "SUCCESS_KALI"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] == 0
        assert "Hello from Kali Linux" in res["stdout"]
        assert res["migrated"] is False
        assert len(res["migrations"]) == 0

# TEST 2: Configured Kali environment failure. (Automatic migration to Parrot)
def test_scenario_2_kali_env_failure_auto_migration(mock_controller):
    # Program with header not available on Kali, but available on Parrot
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("Test 2: Success on Parrot OS via Failover!\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "online"}):

        res = mock_controller.run_program(
            job_id="test_case_2",
            title="Test 2",
            source_code=code,
            compiler_flags=["-Wall", "-O2"]
        )

        assert res["status"] == "SUCCESS_PARROT_MIGRATED"
        assert res["executed_on"] == "Parrot OS"
        assert res["exit_code"] == 0
        assert "Success on Parrot OS" in res["stdout"]
        assert res["migrated"] is True
        assert len(res["migrations"]) == 1
        assert res["migrations"][0]["from_env"] == "Kali Linux"
        assert res["migrations"][0]["to_env"] == "Parrot OS"
        assert res["migrations"][0]["success"] is True

# TEST 3: C syntax error. (Compiler error returned, NO migration)
def test_scenario_3_c_syntax_error_no_migration(mock_controller):
    code = """#include <stdio.h>
int main() {
    printf("Broken syntax") // Missing semicolon
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_case_3",
            title="Test 3",
            source_code=code,
            compiler_flags=["-Wall", "-O2"]
        )

        assert res["status"] == "FAILED_KALI_NORMAL"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] != 0
        assert res["migrated"] is False
        assert len(res["migrations"]) == 0
        assert res["failure_type"] == "PROGRAM_ERROR"
        assert "Syntax Error" in res["failure_reason"] or "syntax" in res["failure_reason"].lower()

# TEST 4: Parrot unavailable. (Clear migration failure message)
def test_scenario_4_parrot_unavailable(mock_controller):
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    return 0;
}
"""
    # Simulate Kali failing due to missing header, but Parrot health check returns offline
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "offline", "error": "Connection refused"}):

        res = mock_controller.run_program(
            job_id="test_case_4",
            title="Test 4",
            source_code=code,
            simulate_parrot_offline=True
        )

        assert res["status"] == "MIGRATION_FAILED"
        assert res["migrated"] is False
        assert any(w in res["failure_reason"].lower() for w in ["unavailab", "offline"])
        # Verify migration record indicates failed migration attempt
        assert len(res["migrations"]) == 1
        assert res["migrations"][0]["success"] is False

# TEST 5: Program timeout. (Timeout recorded and displayed)
def test_scenario_5_program_timeout(mock_controller):
    code = """#include <stdio.h>
int main() {
    while(1) {}
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_case_5",
            title="Test 5",
            source_code=code,
            timeout_seconds=0.5
        )

        assert res["status"] == "TIMEOUT"
        assert res["failure_type"] == "TIMEOUT"
        assert res["migrated"] is False
        assert "timeout" in res["failure_reason"].lower()
