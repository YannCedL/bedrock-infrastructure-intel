# test du moteur d infrastructures OSM
from unittest.mock import patch, MagicMock
from bedrock_infrastructure_intel.osm import query_infrastructure

def test_query_infrastructure():
    # Test avec reponse mockee garantissant une execution rapide et deterministe
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "elements": [
            {
                "id": 12345,
                "type": "node",
                "lat": 48.8566,
                "lon": 2.3522,
                "tags": {
                    "name": "Poste Source Enedis",
                    "power": "substation",
                    "operator": "Enedis"
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        contract = query_infrastructure(48.8566, 2.3522)
        assert contract is not None
        assert contract.result["total_elements"] == 1
        assert contract.result["zero_fake_data"] is True
        assert len(contract.evidence) >= 1
        assert contract.result["elements"][0]["category"] == "energy"
