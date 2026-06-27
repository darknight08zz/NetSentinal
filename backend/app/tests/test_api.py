from fastapi.testclient import TestClient
from backend.app.main import app

# Create a test client
# Note: Since lifespan (startup/shutdown) handles mongo connection, 
# TestClient runs lifespan automatically when used as a context manager.

def test_get_stats_summary():
    with TestClient(app) as client:
        response = client.get("/api/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "active_alerts" in data

def test_get_topology():
    with TestClient(app) as client:
        response = client.get("/api/topology")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
