from fastapi.testclient import TestClient
from rapidagent.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_llms_list():
    r = client.get("/llms")
    assert r.status_code == 200
    data = r.json()
    assert "llms" in data
    assert "default" in data

def test_echo_chat():
    payload = {
        "messages": [{"role": "user", "content": "Hello RapidAgent"}],
        "llm": "echo"
    }
    r = client.post("/requests/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["messages"][-1]["content"] == "Hello RapidAgent"
