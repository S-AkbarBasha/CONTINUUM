"""
End-to-End System Integration Verifier for CONTINUUM
Spawns the Kali Agent, Parrot Agent, and CONTINUUM Controller over live HTTP ports (8001, 8002, 8000),
verifies all 5 core continuity scenarios, and cleanly terminates.
"""
import sys
import time
import subprocess
import httpx

CONTROLLER_URL = "http://127.0.0.1:8000"
KALI_URL = "http://127.0.0.1:8001"
PARROT_URL = "http://127.0.0.1:8002"

def main():
    print("=" * 65)
    print("   CONTINUUM - Full System End-to-End Live HTTP Verification")
    print("=" * 65)

    processes = []
    try:
        # 1. Start Kali Agent
        print("[1/3] Starting Kali Linux Agent (Port 8001)...")
        p_kali = subprocess.Popen([sys.executable, "-m", "uvicorn", "agents.kali_agent.agent:app", "--port", "8001", "--log-level", "warning"])
        processes.append(p_kali)

        # 2. Start Parrot Agent
        print("[2/3] Starting Parrot OS Agent (Port 8002)...")
        p_parrot = subprocess.Popen([sys.executable, "-m", "uvicorn", "agents.parrot_agent.agent:app", "--port", "8002", "--log-level", "warning"])
        processes.append(p_parrot)

        # 3. Start CONTINUUM Central Controller
        print("[3/3] Starting CONTINUUM Controller (Port 8000)...")
        p_ctrl = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--log-level", "warning"])
        processes.append(p_ctrl)

        # Wait for servers to bind
        time.sleep(2.5)

        # Verify Agent Health over HTTP
        print("\n[*] Probing Agent Health via Controller API...")
        res = httpx.get(f"{CONTROLLER_URL}/api/health/agents", timeout=5.0)
        assert res.status_code == 200, f"Health check failed: {res.text}"
        agents = res.json()
        print(f"    -> Discovered {len(agents)} agents: {[a['agent_name'] + ' (' + a['status'] + ')' for a in agents]}")

        # TEST 1: Valid C Program in Kali
        print("\n[*] Running TEST 1: Valid C program on Kali Linux (Primary)...")
        res1 = httpx.post(f"{CONTROLLER_URL}/api/demo/run-test/test_1", timeout=15.0)
        assert res1.status_code == 200, res1.text
        data1 = res1.json()
        print(f"    -> Status: {data1['status']} | Executed On: {data1['executed_on']} | Exit Code: {data1['exit_code']}")
        print(f"    -> Migrated: {data1['migrated']}")
        assert data1["status"] == "SUCCESS_KALI", f"Expected SUCCESS_KALI, got {data1['status']}"
        assert data1["executed_on"] == "Kali Linux"
        assert not data1["migrated"]
        print("    [PASS] Test 1: Successful Kali execution without migration.")

        # TEST 2: Environment Incompatibility -> Auto Failover to Parrot OS
        print("\n[*] Running TEST 2: Missing dependency on Kali -> Automatic failover to Parrot OS...")
        res2 = httpx.post(f"{CONTROLLER_URL}/api/demo/run-test/test_2", timeout=15.0)
        assert res2.status_code == 200, res2.text
        data2 = res2.json()
        print(f"    -> Status: {data2['status']} | Executed On: {data2['executed_on']} | Exit Code: {data2['exit_code']}")
        print(f"    -> Migrated: {data2['migrated']} | Failure Reason: {data2['failure_reason']}")
        assert data2["status"] == "SUCCESS_PARROT_MIGRATED", f"Expected SUCCESS_PARROT_MIGRATED, got {data2['status']}"
        assert data2["executed_on"] == "Parrot OS"
        assert data2["migrated"] is True
        assert len(data2["migrations"]) == 1
        print("    [PASS] Test 2: Automatic failover from Kali to Parrot completed successfully.")

        # TEST 3: C Syntax Error -> No Migration
        print("\n[*] Running TEST 3: C Syntax Error (Compiler Error -> NO migration)...")
        res3 = httpx.post(f"{CONTROLLER_URL}/api/demo/run-test/test_3", timeout=15.0)
        assert res3.status_code == 200, res3.text
        data3 = res3.json()
        print(f"    -> Status: {data3['status']} | Failure Type: {data3['failure_type']}")
        print(f"    -> Migrated: {data3['migrated']} | Reason: {data3['failure_reason']}")
        assert data3["status"] == "FAILED_KALI_NORMAL"
        assert data3["failure_type"] == "PROGRAM_ERROR"
        assert not data3["migrated"]
        print("    [PASS] Test 3: Normal syntax error caught; migration avoided.")

        # TEST 4: Backup Environment (Parrot OS) Unavailable
        print("\n[*] Running TEST 4: Kali environment error when Parrot OS is unavailable...")
        res4 = httpx.post(f"{CONTROLLER_URL}/api/demo/run-test/test_4", timeout=15.0)
        assert res4.status_code == 200, res4.text
        data4 = res4.json()
        print(f"    -> Status: {data4['status']} | Failure Reason: {data4['failure_reason']}")
        assert data4["status"] == "MIGRATION_FAILED"
        assert not data4["migrated"]
        print("    [PASS] Test 4: Clear migration failure message returned when backup is offline.")

        # TEST 5: Program Timeout Protection
        print("\n[*] Running TEST 5: Infinite loop / Timeout watchdog...")
        res5 = httpx.post(f"{CONTROLLER_URL}/api/demo/run-test/test_5", timeout=15.0)
        assert res5.status_code == 200, res5.text
        data5 = res5.json()
        print(f"    -> Status: {data5['status']} | Failure Type: {data5['failure_type']}")
        assert data5["status"] == "TIMEOUT"
        assert data5["failure_type"] == "TIMEOUT"
        assert not data5["migrated"]
        print("    [PASS] Test 5: Watchdog timeout correctly terminated hung process.")

        # TEST 6: Program with scanf() Stdin Input on Kali
        print("\n[*] Running TEST 6: C program with scanf() and multiline stdin on Kali Linux...")
        scanf_code = """#include <stdio.h>

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
        res6 = httpx.post(f"{CONTROLLER_URL}/api/jobs/run", json={
            "title": "Live Stdin Sum Test",
            "source_code": scanf_code,
            "stdin": "10\n20"
        }, timeout=15.0)
        assert res6.status_code == 200, res6.text
        data6 = res6.json()
        print(f"    -> Status: {data6['status']} | Executed On: {data6['executed_on']} | Exit Code: {data6['exit_code']}")
        print(f"    -> Output: {data6['stdout'].strip()}")
        assert data6["status"] == "SUCCESS_KALI"
        assert "Sum = 30" in data6["stdout"]
        assert not data6["migrated"]
        print("    [PASS] Test 6: Stdin data successfully passed to executable; Sum = 30 verified.")

        # TEST 7: Program with scanf() Stdin Input with Auto Failover to Parrot OS
        print("\n[*] Running TEST 7: C program with scanf() during automatic failover (preserves stdin)...")
        res7 = httpx.post(f"{CONTROLLER_URL}/api/jobs/run", json={
            "title": "Live Stdin Failover Test",
            "source_code": scanf_code,
            "stdin": "10\n20",
            "simulate_kali_env_failure": True,
            "simulate_failure_reason": "Live test Kali environment fault."
        }, timeout=15.0)
        assert res7.status_code == 200, res7.text
        data7 = res7.json()
        print(f"    -> Status: {data7['status']} | Executed On: {data7['executed_on']} | Exit Code: {data7['exit_code']}")
        print(f"    -> Output: {data7['stdout'].strip()}")
        print(f"    -> Migrated: {data7['migrated']} | Migrations: {len(data7['migrations'])}")
        assert data7["status"] == "SUCCESS_PARROT_MIGRATED"
        assert data7["executed_on"] == "Parrot OS"
        assert data7["migrated"] is True
        assert "Sum = 30" in data7["stdout"]
        assert len(data7["migrations"]) == 1
        print("    [PASS] Test 7: Failover preserved stdin and restored execution on Parrot OS.")

        print("\n" + "=" * 65)
        print("   ALL CONTINUITY & STDIN SCENARIOS VERIFIED OVER LIVE REST APIS!")
        print("=" * 65)

    finally:
        print("\n[*] Shutting down test processes...")
        for p in processes:
            p.terminate()
            try:
                p.wait(timeout=2)
            except Exception:
                p.kill()
        print("[*] Cleanup complete.")

if __name__ == "__main__":
    main()
