# Tests unitaires pour BEDROCK Infrastructure Intel avec nouvelles categories
from unittest.mock import patch, MagicMock
from bedrock_infrastructure_intel.osm import (
    query_infrastructure,
    build_overpass_query,
    get_available_categories,
    _classify_element
)

def test_build_overpass_query():
    q_all = build_overpass_query(48.8566, 2.3522, 2000, "all")
    assert "power" in q_all
    assert "pipeline" in q_all
    assert "military" in q_all
    assert "storage_tank" in q_all
    assert "around:2000,48.8566,2.3522" in q_all


def test_classify_element_extended():
    # 1. Energie & source primaire
    res_plant = _classify_element({"power": "plant", "plant:source": "nuclear"})
    assert res_plant["category"] == "energy"
    assert res_plant["details"]["primary_source"] == "nuclear"

    # 2. Pipeline
    res_pipe = _classify_element({"man_made": "pipeline", "substance": "gas"})
    assert res_pipe["category"] == "energy"
    assert res_pipe["details"]["pipeline_substance"] == "gas"

    # 3. Stockage dangereux
    res_tank = _classify_element({"man_made": "storage_tank", "content": "oil"})
    assert res_tank["category"] == "hazmat_seveso"
    assert res_tank["details"]["content"] == "oil"

    # 4. Militaire
    res_mil = _classify_element({"landuse": "military", "military": "airfield"})
    assert res_mil["category"] == "military_defense"
    assert res_mil["icon"] == "🛡️"

    # 5. Prison
    res_prison = _classify_element({"amenity": "prison"})
    assert res_prison["category"] == "military_defense"

    # 6. Douane
    res_douane = _classify_element({"barrier": "border_control"})
    assert res_douane["category"] == "military_defense"

    # 7. Eau & Barrage
    res_dam = _classify_element({"waterway": "dam"})
    assert res_dam["category"] == "natural_hazards_water"
    assert res_dam["icon"] == "💧"

    # 8. Mines
    res_mine = _classify_element({"landuse": "quarry", "resource": "gravel"})
    assert res_mine["category"] == "mining"
    assert res_mine["details"]["resource"] == "gravel"


def test_get_available_categories():
    cats = get_available_categories()
    assert "energy" in cats
    assert "hazmat_seveso" in cats
    assert "mining" in cats
    assert "military_defense" in cats
    assert "natural_hazards_water" in cats
    assert "submarine_telecom" in cats
    assert "transport" in cats


def test_query_infrastructure_contract():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "elements": [
            {
                "id": 112233,
                "type": "node",
                "lat": 48.8566,
                "lon": 2.3522,
                "tags": {
                    "name": "Centrale Nucléaire de Paluel",
                    "power": "plant",
                    "plant:source": "nuclear"
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        contract = query_infrastructure(48.8566, 2.3522, radius_m=500)
        assert contract is not None
        assert contract.result["total_elements"] == 1
        assert contract.result["zero_fake_data"] is True
        assert contract.result["elements"][0]["technical_details"]["primary_source"] == "nuclear"
        assert "risk_assessment" in contract.result
        assert contract.result["risk_assessment"]["composite_risk_score"] > 0
