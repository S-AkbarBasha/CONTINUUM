import pytest
from unittest.mock import patch
from starlette.testclient import TestClient

from backend.main import app
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


# 1. KALI SUCCESS: Normal execution succeeds on Kali; no confirmation question.
def test_user_approved_flow_kali_success(mock_controller):
    code = """#include <stdio.h>
int main() {
    printf("Success on Kali!\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_kali_success_1",
            title="Kali Success",
            source_code=code,
            auto_migrate=False
        )

        assert res["status"] == "SUCCESS_KALI"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] == 0
        assert "Success on Kali!" in res["stdout"]
        assert res["migrated"] is False
        assert len(res["migrations"]) == 0
        assert res["status"] != "AWAITING_APPROVAL"


# 2. ENVIRONMENT FAILURE FOLLOWED BY YES: User approves failover -> executes on Parrot OS
def test_user_approved_flow_env_failure_followed_by_yes(mock_controller):
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("Successfully executed on Parrot OS after user approval!\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "online"}):

        # Initial run on Kali with user-approval flow enabled
        res_initial = mock_controller.run_program(
            job_id="test_env_yes_1",
            title="Env Failure Yes",
            source_code=code,
            auto_migrate=False
        )

        # Step 4 & 5: Kali encounters environment failure, stops auto-migration, awaits approval
        assert res_initial["status"] == "AWAITING_APPROVAL"
        assert res_initial["executed_on"] == "Kali Linux"
        assert res_initial["failure_type"] == "ENVIRONMENT_FAILURE"
        assert res_initial["migrated"] is False

        # Step 6: User clicks "Yes, Migrate to Parrot"
        res_migrated = mock_controller.approve_migration("test_env_yes_1")

        assert res_migrated["status"] == "SUCCESS_PARROT_MIGRATED"
        assert res_migrated["executed_on"] == "Parrot OS"
        assert res_migrated["exit_code"] == 0
        assert "Successfully executed on Parrot OS after user approval!" in res_migrated["stdout"]
        assert res_migrated["migrated"] is True
        assert len(res_migrated["migrations"]) == 1
        assert res_migrated["migrations"][0]["from_env"] == "Kali Linux"
        assert res_migrated["migrations"][0]["to_env"] == "Parrot OS"
        assert res_migrated["migrations"][0]["success"] is True

        # Check timeline audit trail
        timeline = res_migrated["timeline"]
        stages = [e["stage"] for e in timeline]
        assert "AWAITING_APPROVAL" in stages
        assert "USER_DECISION" in stages
        assert "PARROT_RESULT" in stages


# 3. ENVIRONMENT FAILURE FOLLOWED BY NO: User declines failover -> stays on Kali
def test_user_approved_flow_env_failure_followed_by_no(mock_controller):
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    return 0;
}
"""
    dispatch_mock = patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch)
    with dispatch_mock as mock_dispatch:
        # Initial run on Kali
        res_initial = mock_controller.run_program(
            job_id="test_env_no_1",
            title="Env Failure No",
            source_code=code,
            auto_migrate=False
        )

        assert res_initial["status"] == "AWAITING_APPROVAL"
        assert res_initial["executed_on"] == "Kali Linux"

        # Record how many times dispatch was called (only once for Kali)
        call_count_before = mock_dispatch.call_count
        assert call_count_before == 1

        # Step 6: User clicks "No, Stay on Kali"
        res_declined = mock_controller.decline_migration("test_env_no_1")

        # Do NOT contact Parrot to execute the program
        assert mock_dispatch.call_count == call_count_before
        assert res_declined["status"] == "MIGRATION_DECLINED"
        assert res_declined["executed_on"] == "Kali Linux"
        assert res_declined["migrated"] is False
        assert "parrot_exclusive.h" in res_declined["failure_reason"]

        # Audit trail records user's decision to decline
        timeline = res_declined["timeline"]
        stages = [e["stage"] for e in timeline]
        assert "USER_DECISION" in stages
        user_dec_event = next(e for e in timeline if e["stage"] == "USER_DECISION")
        assert "declined" in user_dec_event["message"].lower()

        # Check migrations table
        migrations = res_declined["migrations"]
        assert len(migrations) == 1
        assert migrations[0]["success"] is False
        assert "declined" in migrations[0]["reason"].lower()


# 4. SYNTAX ERROR: Ordinary program errors are NOT treated as environment failures
def test_user_approved_flow_syntax_error(mock_controller):
    code = """#include <stdio.h>
int main() {
    printf("Missing semicolon")
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        res = mock_controller.run_program(
            job_id="test_syntax_error_1",
            title="Syntax Error",
            source_code=code,
            auto_migrate=False
        )

        # Fails normally on Kali; never transitions to AWAITING_APPROVAL
        assert res["status"] == "FAILED_KALI_NORMAL"
        assert res["executed_on"] == "Kali Linux"
        assert res["exit_code"] != 0
        assert res["migrated"] is False
        assert res["failure_type"] == "PROGRAM_ERROR"
        assert len(res["migrations"]) == 0


# 5. PARROT UNAVAILABLE AFTER APPROVAL: User approves, but Parrot is offline -> clear failure
def test_user_approved_flow_parrot_unavailable_after_approval(mock_controller):
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "offline", "error": "Connection refused"}):

        # Initial run on Kali
        res_initial = mock_controller.run_program(
            job_id="test_parrot_offline_1",
            title="Parrot Offline Test",
            source_code=code,
            auto_migrate=False,
            simulate_parrot_offline=True
        )

        assert res_initial["status"] == "AWAITING_APPROVAL"

        # User approves migration
        res_after = mock_controller.approve_migration("test_parrot_offline_1", simulate_parrot_offline=True)

        assert res_after["status"] == "MIGRATION_FAILED"
        assert res_after["migrated"] is False
        assert any(w in res_after["failure_reason"].lower() for w in ["unavailab", "offline", "unreachable"])
        assert len(res_after["migrations"]) == 1
        assert res_after["migrations"][0]["success"] is False


# 6. DUPLICATE APPROVAL REQUESTS: Multiple consecutive clicks are handled safely and idempotently
def test_user_approved_flow_duplicate_approval_requests(mock_controller):
    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("Duplicate approval test\\n");
    return 0;
}
"""
    with patch.object(mock_controller, "_dispatch_to_agent", side_effect=simulated_dispatch) as mock_dispatch, \
         patch.object(mock_controller, "check_agent_health", return_value={"status": "online"}):

        # Initial run
        res_initial = mock_controller.run_program(
            job_id="test_dup_approval_1",
            title="Duplicate Approval",
            source_code=code,
            auto_migrate=False
        )
        assert res_initial["status"] == "AWAITING_APPROVAL"

        # First approval
        res_first = mock_controller.approve_migration("test_dup_approval_1")
        assert res_first["status"] == "SUCCESS_PARROT_MIGRATED"
        assert mock_dispatch.call_count == 2  # 1 for Kali, 1 for Parrot

        # Second approval (simulating user clicking button again)
        res_second = mock_controller.approve_migration("test_dup_approval_1")
        assert res_second["status"] == "SUCCESS_PARROT_MIGRATED"

        # Third approval
        res_third = mock_controller.resolve_migration("test_dup_approval_1", approved=True)
        assert res_third["status"] == "SUCCESS_PARROT_MIGRATED"

        # Parrot was NOT dispatched multiple times
        assert mock_dispatch.call_count == 2


# 7. FASTAPI API INTEGRATION: Test /api/jobs/run and /api/jobs/{job_id}/decision endpoints
def test_api_user_approval_endpoints():
    client = TestClient(app)
    from controller.failover_manager import failover_controller

    code = """#include <stdio.h>
#include <parrot_exclusive.h>
int main() {
    printf("API Approval Test\\n");
    return 0;
}
"""
    with patch.object(failover_controller, "_dispatch_to_agent", side_effect=simulated_dispatch), \
         patch.object(failover_controller, "check_agent_health", return_value={"status": "online"}):

        # 1. Submit job via API
        response = client.post("/api/jobs/run", json={
            "title": "API Test",
            "source_code": code
        })
        assert response.status_code == 200
        data = response.json()
        job_id = data["id"]
        assert data["status"] == "AWAITING_APPROVAL"

        # 2. Approve migration via decision endpoint
        dec_resp = client.post(f"/api/jobs/{job_id}/decision", json={"approved": True})
        assert dec_resp.status_code == 200
        dec_data = dec_resp.json()
        assert dec_data["status"] == "SUCCESS_PARROT_MIGRATED"
        assert dec_data["migrated"] is True

        # 3. Duplicate approval request via API
        dup_resp = client.post(f"/api/jobs/{job_id}/decision", json={"approved": True})
        assert dup_resp.status_code == 200
        assert dup_resp.json()["status"] == "SUCCESS_PARROT_MIGRATED"
