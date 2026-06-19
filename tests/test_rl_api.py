import pytest
from fastapi.testclient import TestClient
from api.main import app
import os

client = TestClient(app)

def test_rl_status():
    response = client.get("/api/rl/status")
    assert response.status_code == 200
    data = response.json()
    assert "model_exists" in data

def test_rl_session_flow():
    # Only test if model exists to avoid failing CI
    status = client.get("/api/rl/status").json()
    if not status.get("model_exists", False):
        pytest.skip("RL model not trained, skipping session tests")
        
    start_req = {
        "latitude": 12.9789,
        "longitude": 77.5998,
        "event_type": "protest",
        "duration_hours": 2.0,
        "weather_rain": False
    }
    
    res = client.post("/api/rl/start-session", json=start_req)
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert "junctions" in data
    
    session_id = data["session_id"]
    
    # test next action
    act_res = client.post("/api/rl/next-action", json={"session_id": session_id})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert "actions" in act_data
    assert "metrics" in act_data
    
    # test end session
    end_res = client.post("/api/rl/end-session", json={"session_id": session_id})
    assert end_res.status_code == 200
