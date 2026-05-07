# test du moteur d'infrastructures OSM
from bedrock_infrastructure_intel.osm import query_infrastructure

def test_query_infrastructure():
    contract = query_infrastructure(48.8566, 2.3522)
    assert contract is not None
    assert contract.result["total_elements"] >= 1
    assert len(contract.evidence) >= 1
