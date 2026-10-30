#!/usr/bin/env bash
# ===================================================================
# CONTINUUM Kali Linux Agent Setup & Launcher
# Run this script inside the Kali Linux VirtualBox VM
# ===================================================================

set -e

echo "=== CONTINUUM: Initializing Kali Linux Execution Agent ==="

# Check GCC availability
if ! command -v gcc &> /dev/null; then
    echo "[!] GCC not found. Installing build-essential..."
    sudo apt-get update && sudo apt-get install -y build-essential python3 python3-pip python3-venv
fi

# Locate project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure dependencies installed
if ! python3 -c "import fastapi, uvicorn" &> /dev/null; then
    echo "[*] Installing Python agent dependencies..."
    pip3 install --break-system-packages fastapi uvicorn pydantic requests httpx || pip3 install fastapi uvicorn pydantic requests httpx
fi

# Print network IP info for convenience
echo "---------------------------------------------------------"
echo "Detected IP Addresses on Kali VM:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' || true
echo "---------------------------------------------------------"

PORT="${PORT:-8001}"
HOST="${HOST:-0.0.0.0}"

echo "[*] Starting Kali Linux Agent on $HOST:$PORT..."
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
python3 -m uvicorn agents.kali_agent.agent:app --host "$HOST" --port "$PORT"
