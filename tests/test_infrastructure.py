from bedrock_infrastructure_intel import query_infrastructure

def test_query_infrastructure():
    c = query_infrastructure(48.8566, 2.3522, 500)
    assert c.result["lat"] == 48.8566
    assert "features" in c.result
    assert c.confidence > 0.9
