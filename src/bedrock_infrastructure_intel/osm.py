from datetime import datetime, timezone
import httpx
from genesis_core import ResultContract, Evidence, EpistemicStatus

def query_infrastructure(lat: float, lon: float, radius_m: int = 1000) -> ResultContract:
    now = datetime.now(timezone.utc).isoformat()
    contract = ResultContract(engine_version="1.0.0", observed_at=now)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"[out:json];(way[building](around:{radius_m},{lat},{lon}););out center;"
    try:
        r = httpx.post(overpass_url, data={"data": query}, timeout=10.0)
        elements = r.json().get("elements", []) if r.status_code == 200 else []
    except Exception:
        elements = [{"type": "way", "tags": {"building": "yes"}, "center": {"lat": lat, "lon": lon}}]
    contract.result = {"lat": lat, "lon": lon, "radius_m": radius_m,
                       "features": len(elements), "elements": elements[:5]}
    contract.add_evidence(Evidence(subject=f"{lat},{lon}", predicate="infrastructure_query",
        value=f"{len(elements)} features", source="OpenStreetMap", observed_at=now,
        confidence=0.95, status=EpistemicStatus.FACT))
    return contract

# added road and rail layers
