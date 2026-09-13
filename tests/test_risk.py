# Tests unitaires pour la matrice de risque BEDROCK
from bedrock_infrastructure_intel.risk import compute_zone_risk_matrix

def test_empty_elements_risk():
    res = compute_zone_risk_matrix([], 3000)
    assert res["composite_risk_score"] == 0
    assert res["risk_level"] == "FAIBLE"
    assert res["critical_alerts_count"] == 0


def test_hazmat_and_nuclear_risk():
    elements = [
        {
            "name": "Dépôt Pétrolier Seveso",
            "category": "hazmat_seveso",
            "type": "seveso_storage_tank",
            "technical_details": {"content": "oil"}
        },
        {
            "name": "Centrale Nucléaire",
            "category": "energy",
            "type": "power_plant",
            "technical_details": {"primary_source": "nuclear"}
        }
    ]
    res = compute_zone_risk_matrix(elements, 3000)
    assert res["composite_risk_score"] > 20
    assert res["dimensions"]["hazmat_seveso"] >= 25
    assert res["dimensions"]["energy_criticality"] >= 35
    assert res["critical_alerts_count"] >= 2
