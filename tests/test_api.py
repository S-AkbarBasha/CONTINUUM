import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()

client = TestClient(app)

def test_root_serves_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "CONTINUUM" in response.text

def test_get_demo_presets():
    response = client.get("/api/demo/presets")
    assert response.status_code == 200
    data = response.json()
    assert "test_1" in data
    assert "test_2" in data
    assert "test_3" in data
    assert "test_4" in data
    assert "test_5" in data

def test_get_agent_config():
    response = client.get("/api/config/agents")
    assert response.status_code == 200
    data = response.json()
    assert "kali_agent_url" in data
    assert "parrot_agent_url" in data

def test_update_agent_config():
    response = client.post("/api/config/agents", json={
        "kali_agent_url": "http://192.168.56.101:8001",
        "parrot_agent_url": "http://192.168.56.102:8002"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["kali_agent_url"] == "http://192.168.56.101:8001"
    assert data["parrot_agent_url"] == "http://192.168.56.102:8002"

    # Reset back to localhost for local tests
    client.post("/api/config/agents", json={
        "kali_agent_url": "http://127.0.0.1:8001",
        "parrot_agent_url": "http://127.0.0.1:8002"
    })

def test_list_jobs_endpoint():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_migrations_endpoint():
    response = client.get("/api/migrations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_run_job_with_stdin_api():
    from unittest.mock import patch
    from tests.test_stdin import simulated_dispatch
    from controller.failover_manager import failover_controller

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
    with patch.object(failover_controller, "_dispatch_to_agent", side_effect=simulated_dispatch):
        response = client.post("/api/jobs/run", json={
            "title": "API Stdin Test",
            "source_code": code,
            "stdin": "10\n20"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS_KALI"
        assert "Sum = 30" in data["stdout"]
        assert data["stdin"] == "10\n20" or data["stdin_data"] == "10\n20"
