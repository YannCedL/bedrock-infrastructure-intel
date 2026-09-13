# Moteur d extraction d infrastructures critiques OSINT via OpenStreetMap Overpass API
# Regle ZERO FAKE DATA absolue : 100% de donnees reelles OpenStreetMap, aucun fallback fictif.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from genesis_core import ResultContract, Evidence, EpistemicStatus
from .risk import compute_zone_risk_matrix

logger = logging.getLogger(__name__)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

INFRASTRUCTURE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "energy": {
        "label": "Energie, Centrales & Pipelines",
        "icon": "⚡",
        "tags": [
            'node["power"="substation"]',
            'way["power"="substation"]',
            'node["power"="plant"]',
            'way["power"="plant"]',
            'node["power"="generator"]',
            'way["power"="generator"]',
            'way["man_made"="pipeline"]',
            'node["man_made"="pipeline"]'
        ]
    },
    "hazmat_seveso": {
        "label": "Sites Seveso, Cuves & Torches",
        "icon": "🛢️",
        "tags": [
            'node["man_made"="storage_tank"]',
            'way["man_made"="storage_tank"]',
            'node["man_made"="chimney"]',
            'node["man_made"="flare"]',
            'node["industrial"="chemical"]',
            'way["industrial"="chemical"]'
        ]
    },
    "submarine_telecom": {
        "label": "Cables Sous-Marins & Landing Stations",
        "icon": "🌐",
        "tags": [
            'node["telecom"="cable_landing_station"]',
            'way["telecom"="cable_landing_station"]',
            'node["tower:type"="communication"]',
            'node["telecom"="data_center"]',
            'way["telecom"="data_center"]'
        ]
    },
    "natural_hazards_water": {
        "label": "Barrages, Eau & Zones Submersibles",
        "icon": "💧",
        "tags": [
            'node["man_made"="water_works"]',
            'way["man_made"="water_works"]',
            'node["man_made"="wastewater_plant"]',
            'way["man_made"="wastewater_plant"]',
            'node["waterway"="dam"]',
            'way["waterway"="dam"]',
            'way["flood_prone"="yes"]'
        ]
    },
    "military_defense": {
        "label": "Defense, Prisons & Douanes",
        "icon": "🛡️",
        "tags": [
            'node["landuse"="military"]',
            'way["landuse"="military"]',
            'node["military"]',
            'way["military"]',
            'node["amenity"="prison"]',
            'way["amenity"="prison"]',
            'node["barrier"="border_control"]'
        ]
    },
    "mining": {
        "label": "Carrieres & Mines",
        "icon": "⛏️",
        "tags": [
            'node["landuse"="quarry"]',
            'way["landuse"="quarry"]',
            'node["man_made"="mineshaft"]'
        ]
    },
    "transport": {
        "label": "Transports (Ports, Aeroports, Gares)",
        "icon": "🚢",
        "tags": [
            'node["aeroway"="aerodrome"]',
            'way["aeroway"="aerodrome"]',
            'node["aeroway"="helipad"]',
            'node["harbour"="yes"]',
            'node["industrial"="port"]',
            'way["landuse"="port"]',
            'way["harbour"="yes"]',
            'node["railway"="station"]',
            'way["railway"="station"]'
        ]
    },
    "industrial": {
        "label": "Zones & Batiments Industriels",
        "icon": "🏭",
        "tags": [
            'node["landuse"="industrial"]',
            'way["landuse"="industrial"]',
            'way["building"="industrial"]',
            'node["man_made"="works"]',
            'way["man_made"="works"]',
            'node["industrial"="refinery"]',
            'way["industrial"="refinery"]'
        ]
    },
    "security_health": {
        "label": "Sante & Secours Civils",
        "icon": "🏥",
        "tags": [
            'node["amenity"="hospital"]',
            'way["amenity"="hospital"]',
            'node["amenity"="fire_station"]'
        ]
    }
}


def build_overpass_query(lat: float, lon: float, radius_m: int, category: str = "all") -> str:
    queries_parts: List[str] = []
    cat_key = category.lower().strip()
    if cat_key in INFRASTRUCTURE_CATEGORIES:
        targets = [INFRASTRUCTURE_CATEGORIES[cat_key]]
    else:
        targets = list(INFRASTRUCTURE_CATEGORIES.values())

    for target in targets:
        for t in target["tags"]:
            queries_parts.append(f"{t}(around:{radius_m},{lat},{lon});")

    body = "\n      ".join(queries_parts)
    return f"""[out:json][timeout:14];
(
      {body}
);
out center 80;"""


def _classify_element(tags: Dict[str, Any]) -> Dict[str, Any]:
    power = tags.get("power")
    man_made = tags.get("man_made")
    aeroway = tags.get("aeroway")
    harbour = tags.get("harbour")
    industrial = tags.get("industrial") or tags.get("landuse")
    telecom = tags.get("telecom") or tags.get("tower:type")
    amenity = tags.get("amenity")
    railway = tags.get("railway")
    military = tags.get("military") or (tags.get("landuse") == "military")
    barrier = tags.get("barrier")
    waterway = tags.get("waterway")

    details: Dict[str, Any] = {}

    # 1. Cables sous-marins & stations d'atterrissement
    if telecom == "cable_landing_station":
        details["strategic_role"] = "Atterrissement de cables sous-marins internationaux"
        return {"category": "submarine_telecom", "type": "cable_landing_station", "icon": "🌐", "label": "Câbles Sous-Marins", "details": details}

    # 2. Defense, Prisons & Frontieres
    if military or amenity == "prison" or barrier == "border_control":
        sub = "base_militaire" if military else ("prison" if amenity == "prison" else "poste_douane")
        if military:
            details["military_type"] = tags.get("military") or "site_militaire"
        return {"category": "military_defense", "type": sub, "icon": "🛡️", "label": "Défense & Sécurité", "details": details}

    # 3. Eau, Barrages & Risques de submersion
    if man_made in ("water_works", "wastewater_plant") or waterway == "dam" or tags.get("flood_prone") == "yes":
        sub = "barrage" if waterway == "dam" else ("eau_potable" if man_made == "water_works" else "station_epuration")
        if tags.get("flood_prone") == "yes":
            details["flood_risk"] = "Zone submersible identifiee"
        return {"category": "natural_hazards_water", "type": sub, "icon": "💧", "label": "Eau & Submersion", "details": details}

    # 4. Seveso, Chimie, Stockage Dangereux & Torches
    if man_made in ("storage_tank", "chimney", "flare") or industrial == "chemical":
        details["content"] = tags.get("content") or tags.get("substance") or "matiere_chimique"
        details["seveso_candidate"] = True
        if tags.get("height"):
            details["height_m"] = tags.get("height")
        return {"category": "hazmat_seveso", "type": f"seveso_{man_made or industrial}", "icon": "🛢️", "label": "Site Seveso / Dangereux", "details": details}

    # 5. Carrières & Mines
    if industrial == "quarry" or tags.get("landuse") == "quarry" or man_made == "mineshaft":
        details["resource"] = tags.get("resource") or "minerai_non_specifie"
        return {"category": "mining", "type": "extraction_mining", "icon": "⛏️", "label": "Carrière / Mine", "details": details}

    # 6. Énergie & Pipelines
    if power or man_made == "pipeline":
        if man_made == "pipeline":
            details["pipeline_substance"] = tags.get("substance") or "hydrocarbures"
            return {"category": "energy", "type": "pipeline_network", "icon": "⚡", "label": "Pipeline / Transport", "details": details}
        if power in ("plant", "generator"):
            details["primary_source"] = tags.get("plant:source") or tags.get("generator:source") or "non_specifie"
            details["output_rating"] = tags.get("plant:output:electricity") or tags.get("rating:output")
        if tags.get("voltage"):
            details["voltage_v"] = tags.get("voltage")
        return {"category": "energy", "type": f"power_{power}", "icon": "⚡", "label": "Énergie & Réseaux", "details": details}

    # 7. Transports
    if aeroway:
        return {"category": "transport", "type": f"aero_{aeroway}", "icon": "✈️", "label": "Aviation", "details": details}
    if harbour == "yes" or industrial == "port":
        return {"category": "transport", "type": "maritime_port", "icon": "🚢", "label": "Port Maritime", "details": details}
    if railway:
        return {"category": "transport", "type": f"railway_{railway}", "icon": "🚆", "label": "Ferroviaire", "details": details}

    # 8. Télécoms terrestres
    if telecom or tags.get("man_made") == "mast":
        return {"category": "submarine_telecom", "type": "telecom_infrastructure", "icon": "📡", "label": "Télécom / Data", "details": details}

    # 9. Santé & Urgences
    if amenity in ("hospital", "fire_station"):
        return {"category": "security_health", "type": amenity, "icon": "🏥", "label": "Santé & Secours", "details": details}

    # 10. Industrie générale
    if tags.get("building") == "industrial" or industrial == "industrial":
        return {"category": "industrial", "type": "industrial_site", "icon": "🏭", "label": "Industrie", "details": details}

    return {"category": "other", "type": "infrastructure", "icon": "📍", "label": "Infrastructure", "details": details}


def query_infrastructure(
    lat: float = 48.8566,
    lon: float = 2.3522,
    radius_m: int = 3000,
    category: str = "all"
) -> ResultContract:
    now_iso = datetime.now(timezone.utc).isoformat()
    contract = ResultContract(engine_version="2.2.0", observed_at=now_iso)

    overpass_query = build_overpass_query(lat, lon, radius_m, category)
    elements_list: List[Dict[str, Any]] = []
    endpoint_used = None
    query_success = False
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            headers = {"User-Agent": "BedrockOSINT/2.0 (contact@genesis-intel.com)"}
            with httpx.Client(timeout=14.0) as client:
                r = client.post(endpoint, data={"data": overpass_query}, headers=headers)
                if r.status_code == 200:
                    raw_elements = r.json().get("elements", [])
                    endpoint_used = endpoint
                    query_success = True

                    for el in raw_elements:
                        tags = el.get("tags", {})
                        pos_lat = el.get("lat") or (el.get("center", {}).get("lat"))
                        pos_lon = el.get("lon") or (el.get("center", {}).get("lon"))

                        if pos_lat and pos_lon:
                            meta = _classify_element(tags)
                            name = tags.get("name") or tags.get("operator") or tags.get("brand")
                            elements_list.append({
                                "id": el.get("id"),
                                "osm_type": el.get("type"),
                                "category": meta["category"],
                                "type": meta["type"],
                                "icon": meta["icon"],
                                "category_label": meta["label"],
                                "name": name or f"{meta['label']} #{el.get('id')}",
                                "operator": tags.get("operator"),
                                "technical_details": meta.get("details", {}),
                                "lat": round(pos_lat, 5),
                                "lon": round(pos_lon, 5),
                                "tags": tags
                            })
                    break
        except Exception as e:
            logger.warning(f"Overpass endpoint {endpoint} inaccessible: {e}")
            continue

    cat_counts: Dict[str, int] = {}
    for el in elements_list:
        c = el["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # Matrice de risque composite
    risk_matrix = compute_zone_risk_matrix(elements_list, radius_m)

    contract.result = {
        "center": [lat, lon],
        "radius_m": radius_m,
        "category_filter": category,
        "elements": elements_list,
        "total_elements": len(elements_list),
        "categories_distribution": cat_counts,
        "risk_assessment": risk_matrix,
        "data_source": "OpenStreetMap_Overpass_API_Live",
        "endpoint_used": endpoint_used,
        "query_success": query_success,
        "zero_fake_data": True
    }

    status = EpistemicStatus.FACT if query_success else EpistemicStatus.HYPOTHESIS
    contract.add_evidence(Evidence(
        subject=f"infrastructures_{lat}_{lon}",
        predicate="osm_critical_infrastructure_risk_audit",
        value=f"{len(elements_list)} sites detectes. Score risque zone: {risk_matrix['composite_risk_score']}/100 ({risk_matrix['risk_level']})",
        source="OpenStreetMap_Overpass_Official",
        observed_at=now_iso,
        confidence=0.98 if query_success else 0.50,
        status=status
    ))

    return contract


def get_available_categories() -> Dict[str, Any]:
    return {
        cat_key: {
            "label": data["label"],
            "icon": data["icon"],
            "tags_count": len(data["tags"])
        }
        for cat_key, data in INFRASTRUCTURE_CATEGORIES.items()
    }
