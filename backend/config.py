import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
PROGRAMS_DIR = STORAGE_DIR / "programs"
LOGS_DIR = STORAGE_DIR / "logs"
DB_PATH = STORAGE_DIR / "continuum.db"

# Ensure directories exist
PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "CONTINUUM - Intelligent Cross-OS Program Continuity System"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Primary & Backup execution environments
    # Default is localhost ports 8001 and 8002 for easy local testing / NAT port forwarding,
    # or VirtualBox Host-Only IPs (e.g. 192.168.56.101:8001 and 192.168.56.102:8002)
    kali_agent_url: str = os.getenv("KALI_AGENT_URL", "http://192.168.56.101:8001")
    parrot_agent_url: str = os.getenv("PARROT_AGENT_URL", "http://192.168.56.102:8002")
    
    # Health check & execution timeouts (in seconds)
    agent_health_timeout: float = 2.5
    default_execution_timeout: float = 10.0
    compile_timeout: float = 15.0

settings = Settings()
