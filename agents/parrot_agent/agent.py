import os
import sys
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Add continuum root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.common.base_agent import BaseExecutionAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("parrot_agent")

CONFIG_FILE = Path(__file__).parent / "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

app = FastAPI(
    title=f"CONTINUUM Agent - {config.get('os_name')}",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = BaseExecutionAgent(
    agent_id=config.get("agent_id", "parrot_backup"),
    os_name=config.get("os_name", "Parrot OS 7.3 KDE Security"),
    role=config.get("role", "backup"),
    incompatible_headers=config.get("incompatible_headers", []),
    incompatible_libraries=config.get("incompatible_libraries", [])
)

# Simulation state
is_simulated_down = False

class ExecuteRequest(BaseModel):
    job_id: str
    source_code: str
    compiler_flags: List[str] = Field(default_factory=lambda: ["-Wall", "-O2"])
    stdin: Optional[str] = None
    stdin_data: Optional[str] = ""
    timeout_seconds: Optional[float] = 10.0
    simulate_env_error: Optional[bool] = False
    simulate_failure_reason: Optional[str] = None

@app.get("/health")
def health_check():
    global is_simulated_down
    if is_simulated_down:
        raise HTTPException(status_code=503, detail="Parrot agent is simulated as offline/unreachable.")
    info = executor.get_info()
    return info

@app.post("/execute")
def execute_program(req: ExecuteRequest):
    global is_simulated_down
    if is_simulated_down:
        raise HTTPException(status_code=503, detail="Parrot agent is simulated as offline/unreachable.")
    
    logger.info("Received execution job: %s", req.job_id)
    stdin_val = req.stdin if req.stdin is not None else (req.stdin_data or "")
    result = executor.execute_job(
        job_id=req.job_id,
        source_code=req.source_code,
        compiler_flags=req.compiler_flags,
        stdin_data=stdin_val,
        timeout_seconds=req.timeout_seconds or 10.0,
        simulate_env_error=req.simulate_env_error or False,
        simulate_failure_reason=req.simulate_failure_reason
    )
    return result

@app.post("/simulate-down")
def set_simulated_down():
    global is_simulated_down
    is_simulated_down = True
    return {"status": "simulated_offline", "agent": config.get("os_name")}

@app.post("/simulate-up")
def set_simulated_up():
    global is_simulated_down
    is_simulated_down = False
    return {"status": "online", "agent": config.get("os_name")}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", config.get("port", 8002)))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting CONTINUUM Parrot Agent on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)
