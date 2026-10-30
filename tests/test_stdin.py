import pytest
from unittest.mock import patch
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
    return FailoverManager(kali_url="http://mock-kali:8001", parrot_url="http://mock-parrot:8002")

def simulated_dispatch(base_url, job_id, source_code, compiler_flags, stdin_data, timeout_seconds, simulate_env_error=False, simulate_failure_reason=None):
    if "kali" in base_url or "8001" in base_url:
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
    elif "parrot" in base_url or "8002" in base_url:
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

# TEST 1: Simple C program without scanf -> execute on Kali
def test_case_1_simple_program_without_scanf(mock_controller):
    code = """#include <stdio.h>

int main() {
    printf("Simple program without scanf: OK\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_stdin_case_1",
            title="Simple Program No Scanf",
            source_code=code,
            stdin_data=""
        )

        assert res["status"] == "SUCCESS_KALI"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] == 0
        assert "Simple program without scanf: OK" in res["stdout"]
        assert res["migrated"] is False
        assert len(res["migrations"]) == 0

# TEST 2: C program with scanf -> enter 10 \n 20 -> execute on Kali and display Sum = 30
def test_case_2_scanf_sum_execution_on_kali(mock_controller):
    code = """#include <stdio.h>

int main() {
    int a, b;
    printf("Enter first number: ");
    scanf("%d", &a);

    printf("Enter second number: ");
    scanf("%d", &b);

    printf("Sum = %d\\n", a + b);
    return 0;
}
"""
    stdin_input = "10\n20"

    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_stdin_case_2",
            title="Scanf Sum on Kali",
            source_code=code,
            stdin_data=stdin_input
        )

        assert res["status"] == "SUCCESS_KALI"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] == 0
        assert "Sum = 30" in res["stdout"]
        assert res["stdout"].strip() == "Enter first number: Enter second number: Sum = 30"
        assert res["migrated"] is False
        assert len(res["migrations"]) == 0

# TEST 3: C program with scanf + simulated Kali environment failure -> automatically migrate to Parrot using SAME stdin
def test_case_3_scanf_sum_failover_to_parrot_preserves_stdin(mock_controller):
    code = """#include <stdio.h>

int main() {
    int a, b;
    printf("Enter first number: ");
    scanf("%d", &a);

    printf("Enter second number: ");
    scanf("%d", &b);

    printf("Sum = %d\\n", a + b);
    return 0;
}
"""
    stdin_input = "10\n20"

    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "online"}):

        res = mock_controller.run_program(
            job_id="test_stdin_case_3",
            title="Scanf Sum with Kali Env Failure",
            source_code=code,
            stdin_data=stdin_input,
            simulate_kali_env_failure=True,
            simulate_failure_reason="Simulated GCC toolchain corrupted on Kali Linux."
        )

        # 1. Automatic migration to Parrot OS
        assert res["status"] == "SUCCESS_PARROT_MIGRATED"
        assert res["executed_on"] == "Parrot OS"
        assert res["exit_code"] == 0

        # 2. Used the SAME stdin and displays correct result
        assert "Sum = 30" in res["stdout"]
        assert res["stdout"].strip() == "Enter first number: Enter second number: Sum = 30"
        assert res["migrated"] is True

        # 3. Recorded migration in Execution Logs & Audit Trail
        assert len(res["migrations"]) == 1
        mig = res["migrations"][0]
        assert mig["from_env"] == "Kali Linux"
        assert mig["to_env"] == "Parrot OS"
        assert mig["success"] is True

        # 4. Timeline records the event
        timeline_messages = [t["message"] for t in res["timeline"]]
        assert any("Parrot OS" in msg for msg in timeline_messages)
