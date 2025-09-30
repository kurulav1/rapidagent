from fastapi.testclient import TestClient
from rapidagent.app import app, store

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_tools_endpoint():
    resp = client.get("/tools")
    data = resp.json()
    assert resp.status_code == 200
    assert "tools" in data
    assert any(t["name"] == "search" for t in data["tools"])

def test_agent_endpoints():
    resp = client.post("/agents", json={"name": "UnitTestAgent", "model": "gpt-4o-mini", "tools": []})
    agent_id = resp.json()["id"]

    resp = client.get(f"/agents/{agent_id}")
    assert resp.status_code == 200
    agent = resp.json()["agent"]
    assert agent["name"] == "UnitTestAgent"

    resp = client.get(f"/agents/{agent_id}/traces")
    assert resp.status_code == 200
    assert "traces" in resp.json()
