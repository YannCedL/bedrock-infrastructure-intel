from bedrock_infrastructure_intel.osm import query_infrastructure

def test_query_infrastructure():
    c = query_infrastructure(48.8566, 2.3522, 500)
    assert c.result["center"][0] == 48.8566
    assert "elements" in c.result
    assert c.confidence > 0.9
