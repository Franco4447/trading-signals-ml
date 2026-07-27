"""
Unit tests for FastAPI REST Endpoints and Prediction Payload.
"""
from fastapi.testclient import TestClient

from src.api.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint():
    payload = {
        "candles": [
            {"timestamp": "2024-01-01T00:00:00", "open": 40000.0, "high": 40500.0, "low": 39800.0, "close": 40200.0, "volume": 120.0},
            {"timestamp": "2024-01-01T01:00:00", "open": 40200.0, "high": 41000.0, "low": 40100.0, "close": 40800.0, "volume": 150.0},
            {"timestamp": "2024-01-01T02:00:00", "open": 40800.0, "high": 41500.0, "low": 40700.0, "close": 41400.0, "volume": 200.0}
        ],
        "max_leverage": 5.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "signal_score" in data
    assert "direction" in data
    assert "recommended_leverage" in data
    assert -1.0 <= data["signal_score"] <= 1.0
