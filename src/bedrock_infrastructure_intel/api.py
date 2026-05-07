import os
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from genesis_core import ResultContract
from .osm import query_infrastructure

app = FastAPI(
    title="Bedrock Infrastructure Intel API",
    description="Moteur de Cartographie d'Infrastructures via OpenStreetMap Overpass",
    version="1.0.0"
)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")

@app.get("/", response_class=HTMLResponse)
def index():
    # sert directement l'interface carte leaflet
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Bedrock API - Interface non trouvee</h1>"

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Bedrock", "version": "1.0.0"}

@app.get("/api/v1/infrastructure", response_model=ResultContract)
def get_infra(
    lat: float = Query(48.8566),
    lon: float = Query(2.3522),
    radius_m: int = Query(2000),
    category: str = Query("industrial")
):
    return query_infrastructure(lat, lon, radius_m, category)
