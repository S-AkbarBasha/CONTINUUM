import httpx
from fastapi import APIRouter
from typing import List, Dict, Any

from backend.schemas import AgentHealthResponse, AgentConfigUpdate
from backend.config import settings
from backend.models import upsert_agent_health, get_all_agent_health
from controller.failover_manager import failover_controller

router = APIRouter(prefix="/api", tags=["Agents"])

@router.get("/health/agents", response_model=List[AgentHealthResponse])
def check_all_agents():
    """
    Probes both Kali Linux (Primary) and Parrot OS (Backup) agents,
    evaluating connection status, round-trip latency, and OS/compiler metadata.
    """
    agents = [
        ("kali_primary", "Kali Linux (Primary)", failover_controller.kali_url),
        ("parrot_backup", "Parrot OS (Backup)", failover_controller.parrot_url),
    ]

    results = []
    for agent_id, name, url in agents:
        health_info = failover_controller.check_agent_health(url)
        status = health_info.get("status", "offline")
        os_info = health_info.get("os_name", health_info.get("os", "Linux"))
        compiler_info = health_info.get("compiler", "gcc")
        latency = health_info.get("latency_ms", 0.0)

        upsert_agent_health(
            agent_id=agent_id,
            agent_name=name,
            base_url=url,
            status=status,
            os_info=os_info,
            compiler_info=compiler_info,
            latency_ms=latency,
            details=health_info
        )

        results.append(AgentHealthResponse(
            agent_id=agent_id,
            agent_name=name,
            base_url=url,
            status=status,
            last_checked=health_info.get("last_checked", ""),
            os_info=os_info,
            compiler_info=compiler_info,
            latency_ms=latency,
            details=health_info
        ))

    return results

@router.post("/config/agents")
def update_agent_urls(config: AgentConfigUpdate):
    """
    Dynamically updates the base URLs for Kali and/or Parrot agents.
    Useful for switching between Host-Only network IPs and localhost NAT ports.
    """
    if config.kali_agent_url:
        settings.kali_agent_url = config.kali_agent_url.rstrip("/")
        failover_controller.kali_url = settings.kali_agent_url
    if config.parrot_agent_url:
        settings.parrot_agent_url = config.parrot_agent_url.rstrip("/")
        failover_controller.parrot_url = settings.parrot_agent_url

    return {
        "status": "updated",
        "kali_agent_url": failover_controller.kali_url,
        "parrot_agent_url": failover_controller.parrot_url
    }

@router.get("/config/agents")
def get_agent_config():
    """Returns the currently configured agent URLs."""
    return {
        "kali_agent_url": failover_controller.kali_url,
        "parrot_agent_url": failover_controller.parrot_url
    }
