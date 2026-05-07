from fastapi import FastAPI
from .osm import query_infrastructure

app = FastAPI(title="Bedrock Infrastructure Intel API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Bedrock"}

@app.get("/api/v1/infrastructure")
def infrastructure(lat: float, lon: float, radius_m: int = 1000):
    return query_infrastructure(lat, lon, radius_m)
