# Tests de l API FastAPI de BEDROCK
from fastapi.testclient import TestClient
from bedrock_infrastructure_intel.api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["zero_fake_data"] is True


def test_categories_endpoint():
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "energy" in data["categories"]


def test_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "BEDROCK" in response.text
    assert "map" in response.text


def test_infrastructure_endpoint_radius_validation():
    response = client.get("/api/v1/infrastructure?lat=48.85&lon=2.35&radius_m=25000")
    assert response.status_code == 400
