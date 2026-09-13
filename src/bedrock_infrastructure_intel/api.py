import os
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from genesis_core import ResultContract
from .osm import query_infrastructure, get_available_categories
from .sigint_radio import find_nearby_sdr_receivers


app = FastAPI(
    title="Bedrock Infrastructure Intel API",
    description="Moteur de Cartographie d'Infrastructures Critiques via OpenStreetMap Overpass — Zero Fake Data",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")


@app.get("/", response_class=HTMLResponse)
def index():
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Bedrock API - Interface non trouvee</h1>"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "engine": "Bedrock Infrastructure Intel",
        "version": "2.0.0",
        "zero_fake_data": True
    }


@app.get("/api/v1/categories")
def list_categories():
    """Retourne la liste des categories d'infrastructures critiques interrogeables."""
    return {
        "status": "ok",
        "categories": get_available_categories()
    }


@app.get("/api/v1/infrastructure", response_model=ResultContract)
def get_infra(
    lat: float = Query(48.8566, description="Latitude du point d'interrogation"),
    lon: float = Query(2.3522, description="Longitude du point d'interrogation"),
    radius_m: int = Query(3000, description="Rayon en metres (max 15000)"),
    category: str = Query("all", description="Filtre categorie: all, energy, transport, telecom, industrial, security_health")
):
    if radius_m > 20000:
        raise HTTPException(status_code=400, detail="Le rayon maximal autorise est de 20 000 metres.")
    return query_infrastructure(lat=lat, lon=lon, radius_m=radius_m, category=category)


@app.get("/api/v1/sdr", response_model=ResultContract)
def get_sdr_receivers(
    lat: float = Query(48.8566, description="Latitude cible"),
    lon: float = Query(2.3522, description="Longitude cible"),
    max_results: int = Query(5, description="Nombre de récepteurs SDR les plus proches à renvoyer")
):
    return find_nearby_sdr_receivers(lat=lat, lon=lon, max_results=max_results)

