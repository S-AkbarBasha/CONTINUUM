# CONTINUUM – Test Verification Manual

This document details the step-by-step verification procedures and expected outcomes for the 5 standard test cases required for the CONTINUUM project.

---

## Test Scenario Matrix

| Test ID | Scenario Description | Primary Target | Expected Failure Category | Failover Triggered? | Expected Final Target | Expected Outcome |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **Test 1** | Valid C Program Execution | Kali Linux | `NONE` | **NO** | Kali Linux | Exit Code 0, Output returned |
| **Test 2** | Configured Environment Failure | Kali Linux | `ENVIRONMENT_FAILURE` | **YES (Auto)** | Parrot OS | Exit Code 0, Output returned |
| **Test 3** | C Syntax Error in Source | Kali Linux | `PROGRAM_ERROR` | **NO** | Kali Linux | Exit Code 1, Compiler diagnostic |
| **Test 4** | Backup Environment Unavailable | Kali Linux | `ENVIRONMENT_FAILURE` | **YES (Aborted)** | Kali Linux (Failed) | Migration Failure Alert |
| **Test 5** | Execution Watchdog Timeout | Kali Linux | `TIMEOUT` | **NO** | Kali Linux | Watchdog termination, Exit -9 |

---

## Detailed Test Case Procedures

### Test Case 1: Valid C Program in Kali (Normal Execution)

#### Objective
Verify that a syntactically correct C program compiles and executes in Kali Linux, returning standard output directly without triggering migration.

#### Source Code
```c
#include <stdio.h>

int main() {
    printf("===================================================\n");
    printf("     CONTINUUM PROGRAM CONTINUITY SYSTEM           \n");
    printf("===================================================\n");
    printf("Executing on: Kali Linux (Primary Environment)\n\n");
    
    int numbers[] = {12, 45, 78, 23, 56, 89, 34};
    int n = sizeof(numbers) / sizeof(numbers[0]);
    int max = numbers[0];
    int sum = 0;
    
    for (int i = 0; i < n; i++) {
        if (numbers[i] > max) max = numbers[i];
        sum += numbers[i];
    }
    
    printf("[+] Array Elements Processed: %d\n", n);
    printf("[+] Maximum Value Found     : %d\n", max);
    printf("[+] Total Sum of Elements   : %d\n", sum);
    printf("[+] Average Value           : %.2f\n\n", (float)sum / n);
    printf("[OK] Execution completed with Exit Code 0.\n");
    return 0;
}
```

#### Verification Steps
1. In the CONTINUUM dashboard, click **"⚡ Test 1: Kali Success"**.
2. Click **"EXECUTE ON CONTINUUM"**.
3. **Expected UI State**:
   - Status Badge: `SUCCESS_KALI` (Green).
   - Executed Target: `Kali Linux`.
   - Exit Code: `0`.
   - Pipeline Diagram: `Windows` -> `Kali Linux` -> `Continuity Result` (Active & Green).
   - Migration Status: `NO`.
   - Output Console: Displays array calculation results.

---

### Test Case 2: Configured Kali Environment Failure (Auto Failover to Parrot)

#### Objective
Verify that when a C program requires an environment feature unavailable on Kali Linux (simulated via missing dependency header `<parrot_exclusive.h>`), CONTINUUM automatically detects an `ENVIRONMENT_FAILURE`, verifies Parrot OS availability, restores the source code on Parrot OS, and completes execution seamlessly.

#### Source Code
```c
#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("===================================================\n");
    printf("     CONTINUUM FAILOVER RECOVERY VERIFIED          \n");
    printf("===================================================\n");
    printf("[!] Note: This program failed on Kali Linux due to\n");
    printf("    missing dependency: <parrot_exclusive.h>\n\n");
    printf("[+] CONTINUUM automatically classified the failure\n");
    printf("    as an ENVIRONMENT FAULT, migrated source code,\n");
    printf("    and resumed execution on Parrot OS!\n\n");
    printf("[+] Active OS Environment : Parrot OS 7.3 KDE Security\n");
    printf("[+] Execution Status       : SUCCESS (Recovered)\n");
    printf("[+] User Interventions    : 0 (Fully Automated)\n");
    return 0;
}
```

#### Verification Steps
1. Click **"🔄 Test 2: Auto Failover"**.
2. Click **"EXECUTE ON CONTINUUM"**.
3. **Expected UI State**:
   - Pipeline Diagram: `Kali Linux` turns **Red (Failed)**, the failover cable pulses, and `Parrot OS` turns **Green (Recovered)**.
   - Status Badge: `SUCCESS_PARROT_MIGRATED` (Teal/Green).
   - Executed Target: `Parrot OS`.
   - Failover Migrated?: `⚡ YES (Parrot)`.
   - Timeline: Shows failure analysis on Kali, health check on Parrot, and successful execution on Parrot.
   - Migration Forensics tab: Displays root cause (`fatal error: parrot_exclusive.h: No such file or directory`) and recovery details.

---

### Test Case 3: C Syntax Error (No Migration)

#### Objective
Verify that user programming errors (such as syntax errors and undeclared identifiers) are classified as `PROGRAM_ERROR`, returning compiler diagnostics directly to the user without triggering wasteful failover migrations.

#### Source Code
```c
#include <stdio.h>

int main() {
    printf("Checking compiler syntax validation...\n")  // SYNTAX ERROR: Missing semicolon!
    
    int result = undeclared_variable * 2;              // ERROR: Undeclared identifier!
    printf("Result: %d\n", result);
    return 0;
}
```

#### Verification Steps
1. Click **"⚠️ Test 3: Syntax Error"**.
2. Click **"EXECUTE ON CONTINUUM"**.
3. **Expected UI State**:
   - Status Badge: `FAILED_KALI_NORMAL` (Red).
   - Executed Target: `Kali Linux`.
   - Failover Migrated?: `NO`.
   - Timeline: Reports `RULE_SYNTAX_ERROR` matched. Note: *"Execution halted without migration. Diagnosis: Invalid C code detected."*
   - Compiler Diagnostics tab: Highlights `error: expected ';'` and `error: 'undeclared_variable' undeclared`.

---

### Test Case 4: Backup Environment Unavailable

#### Objective
Verify that when Kali encounters an environment failure but the backup environment (Parrot OS) is unreachable or offline, CONTINUUM issues a clear and graceful migration failure notification rather than hanging.

#### Source Code
```c
#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("Simulating failover when backup node is offline.\n");
    return 0;
}
```

#### Verification Steps
1. Click **"❌ Test 4: Parrot Offline"**.
2. Click **"EXECUTE ON CONTINUUM"**.
3. **Expected UI State**:
   - Status Badge: `MIGRATION_FAILED` (Red).
   - Failure Reason: *"Environment Failure: Required header 'parrot_exclusive.h' is missing... | Failover aborted: Backup environment (Parrot OS) is offline or unreachable."*
   - Timeline: Records `PARROT_RESULT` as error.

---

### Test Case 5: Program Timeout Protection

#### Objective
Verify that long-running or deadlocked C programs (such as `while(1)`) are safely terminated by the execution agent's watchdog timer without hanging the CONTINUUM controller.

#### Source Code
```c
#include <stdio.h>

int main() {
    printf("[*] Starting intensive computation simulation...\n");
    printf("[*] Entering infinite loop to test watchdog timeout...\n");
    fflush(stdout);
    
    volatile int counter = 0;
    while (1) {
        counter++;
    }
    
    return 0;
}
```

#### Verification Steps
1. Click **"⏳ Test 5: Timeout"** (Timeout set to 3.0 seconds).
2. Click **"EXECUTE ON CONTINUUM"**.
3. **Expected UI State**:
   - Status Badge: `TIMEOUT` (Red/Amber).
   - Exit Code: `-9` (Process killed by watchdog).
   - Failover Migrated?: `NO`.
   - Timeline: *"Execution terminated: Process exceeded the allotted runtime timeout of 3.0 seconds."*

---

## Automated Verification

To execute all test suites programmatically:

```powershell
# Run Pytest Suite
python -m pytest tests/ -v

# Run Live HTTP Server Verifier
python scripts/validate_e2e.py
```
