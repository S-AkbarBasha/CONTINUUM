# CONTINUUM – Intelligent Cross-OS Program Continuity System

[![Platform: Windows + VirtualBox](https://img.shields.io/badge/Platform-Windows%20%7C%20Kali%20Linux%20%7C%20Parrot%20OS-blue.svg)](#)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![Language: C + Python](https://img.shields.io/badge/Language-C%20%2B%20Python%203-yellow.svg)](#)
[![Database: SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](#)
[![Tests: Pytest Passing](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)](#)

> **CONTINUUM** is an automated, intelligent cross-OS program continuity system. When a developer submits a C program from Windows, CONTINUUM coordinates transparent execution first in a primary Linux environment (**Kali Linux VM**). If a genuine environment failure occurs (such as agent downtime, missing system dependency, uninstalled library, or configured compatibility restriction), CONTINUUM automatically and seamlessly migrates the C source code, compiler flags, and input data to a secondary execution environment (**Parrot OS VM**) and restarts execution there—without any manual user intervention.

---

## Architecture Overview

```
                                  +-------------------------------------------------------+
                                  |                     Windows Host                      |
                                  |    CONTINUUM Central Controller & Web Dashboard       |
                                  |    (FastAPI: 8000 + SQLite DB + Modern Dark Web UI)   |
                                  +---------------------------+---------------------------+
                                                              |
                                           REST API Dispatch / Health Probes
                                                              |
                     +----------------------------------------+----------------------------------------+
                     | (Primary Execution Node)                                                        | (Backup Execution Node)
                     v                                                                                 v
     +-------------------------------+                                                 +-------------------------------+
     |        Kali Linux VM          |                                                 |           Parrot OS VM        |
     |  (Oracle VirtualBox NIC 2)    |                                                 |   (Oracle VirtualBox NIC 2)   |
     |  IP: 192.168.56.x:8001 or     |                                                 |   IP: 192.168.56.y:8002 or    |
     |  NAT Port Forward 8001        |                                                 |   NAT Port Forward 8002       |
     |                               |                                                 |                               |
     |  - Kali Execution Agent       |                                                 |  - Parrot Execution Agent     |
     |  - GCC Compiler Toolchain     |                                                 |  - GCC Compiler Toolchain     |
     |  - Timeout Watchdog           |                                                 |  - Timeout Watchdog           |
     +---------------+---------------+                                                 +---------------+---------------+
                     |                                                                                 ^
                     | (On Environment Failure)                                                        |
                     +-------------------> [ Intelligent Failure Classifier ] -------------------------+
                                           (Distinguishes Syntax/Logic Errors
                                            from OS Environment Deficiencies)
```

---

## Key Features

1. **Single-Action Trigger**: User writes/loads a C program in the CONTINUUM studio and triggers execution once.
2. **Explainable Rule-Based Failure Classifier**:
   - **Category A (Normal Program Errors)**: Syntax errors, compiler validation failures, runtime assertion/logic errors.
     * *Action*: Returns diagnostics immediately. **No migration**.
   - **Category B (Environment Failures)**: Agent unreachable, toolchain defect, missing system header (`<header.h>`), missing linker library (`-lxyz`), or configured environment incompatibilities.
     * *Action*: Probes Parrot OS health, automatically migrates source code and execution context, resumes execution on Parrot OS, and returns the final output.
3. **Source-Code-Level Recovery (Version 1 Scope)**:
   - Persists source code to `storage/programs/<job_id>.c`.
   - Records execution context (arguments, stdin, timeouts, exit codes) in SQLite `storage/continuum.db`.
   - Generates audit logs in `storage/logs/<job_id>.log`.
4. **Interactive Dark-Tech Dashboard**:
   - Live Kali and Parrot status indicators with latency meters.
   - Interactive animated pipeline flowchart connecting Windows -> Kali -> Parrot -> Result.
   - Microsecond timeline audit log.
   - Tabbed console: Terminal Output, `stdout`, `stderr`, Compiler Diagnostics, and Migration Forensics.
   - One-click presets for all 5 test scenarios.

---

## Directory Structure

```
CONTINUUM/
├── backend/
│   ├── config.py                 # System configuration, timeouts, default agent URLs
│   ├── database.py               # SQLite initialization and connection context
│   ├── models.py                 # DB CRUD methods (jobs, migrations, timeline events)
│   ├── schemas.py                # Pydantic models for API validation
│   ├── main.py                   # FastAPI application & static asset mounter
│   └── routes/
│       ├── jobs.py               # Job submission, status query, and log endpoints
│       ├── agents.py             # Agent health check & URL configuration endpoints
│       └── demo.py               # 1-click test scenario presets (Tests 1 to 5)
├── controller/
│   ├── failure_classifier.py     # Rule-based failure classification engine
│   └── failover_manager.py       # Kali -> Analyze -> Parrot migration orchestrator
├── agents/
│   ├── common/
│   │   └── base_agent.py         # GCC runner, simulation fallback, timeout watchdog
│   ├── kali_agent/
│   │   ├── agent.py              # Kali agent HTTP server (default port 8001)
│   │   └── config.json           # Kali OS profile & incompatible dependency rules
│   └── parrot_agent/
│       ├── agent.py              # Parrot agent HTTP server (default port 8002)
│       └── config.json           # Parrot OS profile
├── frontend/
│   ├── index.html                # Web dashboard markup
│   ├── css/
│   │   └── style.css             # Futuristic dark cyber-theme design system
│   └── js/
│       ├── samples.js            # Preset C programs catalog
│       └── app.js                # State management, pipeline animation, REST client
├── storage/
│   ├── continuum.db              # SQLite persistence database
│   ├── programs/                 # Saved source code files (<job_id>.c)
│   └── logs/                     # Execution audit logs (<job_id>.log)
├── tests/
│   ├── test_classifier.py        # Classifier rule validation
│   ├── test_agent.py             # Agent compilation, execution, and timeout tests
│   ├── test_failover.py          # Integration tests for all 5 continuity scenarios
│   └── test_api.py               # FastAPI REST endpoint tests
├── scripts/
│   ├── run_windows_controller.bat # Windows launcher for CONTINUUM controller
│   ├── run_local_agents.bat      # Windows launcher for local Kali & Parrot agents
│   ├── run_kali_agent.sh         # Linux launcher for Kali VM agent
│   ├── run_parrot_agent.sh       # Linux launcher for Parrot VM agent
│   ├── run_tests.bat             # Automated test runner
│   └── validate_e2e.py           # Live HTTP end-to-end verifier script
├── requirements.txt              # Python dependencies
├── README.md                     # System documentation
└── TESTING.md                    # Comprehensive test verification guide
```

---

## VirtualBox Networking Setup Guide

Oracle VirtualBox must allow the Windows host to send HTTP requests to both virtual machines:
`Windows Host -> Kali Linux Agent` (Port 8001)
`Windows Host -> Parrot OS Agent` (Port 8002)

You can choose either of two networking methods:

### Method 1: Host-Only Adapter (Recommended)

Both VMs (`kali-linux-2026.2-virtualbox-amd64` and `Parrot OS 7.3 KDE Security Edition`) have **NIC 2** attached to the `VirtualBox Host-Only Ethernet Adapter` (subnet `192.168.56.x`).

1. **Verify Host-Only Adapter on Windows**:
   - In PowerShell, run `ipconfig`.
   - Locate `Ethernet adapter VirtualBox Host-Only Network` (typically `192.168.56.1`).
2. **Start the Virtual Machines**:
   - In VirtualBox Manager, start **Kali Linux** and **Parrot OS**.
3. **Retrieve VM IP Addresses**:
   - Inside Kali Linux terminal, run: `ip -4 addr show` (e.g. `192.168.56.101`).
   - Inside Parrot OS terminal, run: `ip -4 addr show` (e.g. `192.168.56.102`).
4. **Launch the Agents in the VMs**:
   - In Kali Linux: `bash scripts/run_kali_agent.sh` (listens on `0.0.0.0:8001`).
   - In Parrot OS: `bash scripts/run_parrot_agent.sh` (listens on `0.0.0.0:8002`).
5. **Configure Agent URLs in CONTINUUM**:
   - Open `http://localhost:8000` on Windows.
   - Click the **Gear icon** (Network Settings) in the top-right corner.
   - Set Kali URL to `http://192.168.56.101:8001` and Parrot URL to `http://192.168.56.102:8002`.
   - Click **Save & Re-check**. Both badges will turn green `ONLINE`.

### Method 2: NAT Port Forwarding (Alternative)

If you prefer using NAT without host-only IP lookups:
1. In VirtualBox, open VM Settings -> **Network** -> **Adapter 1 (NAT)** -> **Advanced** -> **Port Forwarding**.
2. For Kali:
   * Rule Name: `KaliAgent` | Protocol: `TCP` | Host Port: `8001` | Guest Port: `8001`
3. For Parrot:
   * Rule Name: `ParrotAgent` | Protocol: `TCP` | Host Port: `8002` | Guest Port: `8002`
4. Windows will communicate directly via `http://127.0.0.1:8001` and `http://127.0.0.1:8002`.

---

## How to Run the System

### Option A: Local Dev Mode (No VMs Needed)
You can run the full system immediately on Windows using local ports:

```powershell
# Step 1: Install Python dependencies
python -m pip install -r requirements.txt

# Step 2: Start Local Kali (8001) and Parrot (8002) Agents
scripts\run_local_agents.bat

# Step 3: Start CONTINUUM Central Controller (8000)
scripts\run_windows_controller.bat
```

Open your browser and navigate to:
👉 **`http://localhost:8000`**

### Option B: Full Virtual Machine Mode
1. Start **Kali Linux** in VirtualBox and execute:
   ```bash
   bash scripts/run_kali_agent.sh
   ```
2. Start **Parrot OS** in VirtualBox and execute:
   ```bash
   bash scripts/run_parrot_agent.sh
   ```
3. On Windows, start the controller:
   ```powershell
   scripts\run_windows_controller.bat
   ```
4. Open `http://localhost:8000` and configure the VM IPs in the settings dialog.

---

## Automated Test Suite

Run the full automated pytest suite:
```powershell
python -m pytest tests/ -v
```
All 25 tests will validate agent compilation, GCC syntax validation, failure classification, and end-to-end failover scenarios.

Or run the live HTTP end-to-end verifier:
```powershell
python scripts/validate_e2e.py
```
