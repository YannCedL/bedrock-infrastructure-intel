# Moteur d evaluation des risques composites de zone pour BEDROCK Infrastructure Intel
# Regle ZERO FAKE DATA absolue : calcul deterministe base uniquement sur les faits reels observes.

from typing import Any, Dict, List

def compute_zone_risk_matrix(elements: List[Dict[str, Any]], radius_m: int) -> Dict[str, Any]:
    """
    Calcule une matrice de risque composite (0 a 100) pour la zone analysee,
    repartie sur 4 dimensions critiques :
    - Risque Seveso / Chimique / Matieres Dangereuses
    - Risque Criticite Energetique & Reseaux
    - Sensibilite Militaire, Douaniere & Penitentiaire
    - Vulnerabilite Logistique & Transport
    """
    if not elements:
        return {
            "composite_risk_score": 0,
            "risk_level": "FAIBLE",
            "dimensions": {
                "hazmat_seveso": 0,
                "energy_criticality": 0,
                "defense_sovereignty": 0,
                "transport_vulnerability": 0
            },
            "critical_alerts_count": 0,
            "alerts": []
        }

    hazmat_score = 0
    energy_score = 0
    defense_score = 0
    transport_score = 0
    alerts: List[Dict[str, str]] = []

    for el in elements:
        cat = el.get("category")
        tech = el.get("technical_details", {})
        tags = el.get("tags", {})
        sub_type = el.get("type", "")

        # 1. Risque Seveso & Stockage Chimique
        if cat == "hazmat_seveso" or "refinery" in sub_type or tags.get("industrial") == "chemical":
            hazmat_score += 40
            content = tech.get("content", "matiere_dangereuse")
            alerts.append({
                "severity": "CRITIQUE",
                "category": "HAZMAT_SEVESO",
                "message": f"Site Seveso / stockage dangereux detecte : {el.get('name')} (substance: {content})"
            })

        # 2. Criticite Energetique
        if cat == "energy":
            energy_score += 20
            source = tech.get("primary_source")
            if source == "nuclear":
                energy_score += 50
                alerts.append({
                    "severity": "ELEVEE",
                    "category": "NUCLEAR_SITE",
                    "message": f"Site nucleaire civil a proximite : {el.get('name')}"
                })
            elif "pipeline" in sub_type:
                energy_score += 30
                substance = tech.get("pipeline_substance", "hydrocarbures")
                alerts.append({
                    "severity": "ELEVEE",
                    "category": "PIPELINE_NETWORK",
                    "message": f"Reseau de transport par canalisation : {el.get('name')} ({substance})"
                })

        # 3. Defense & Souverainete
        if cat == "military_defense":
            defense_score += 40
            m_type = tech.get("military_type", sub_type)
            alerts.append({
                "severity": "ELEVEE",
                "category": "SOVEREIGN_MILITARY",
                "message": f"Installation militaire / zone de defense souveraine : {el.get('name')} ({m_type})"
            })

        # 4. Transports critiques
        if cat == "transport":
            if "port" in sub_type or "aerodrome" in sub_type:
                transport_score += 25

    # Normalisation sur 100 par dimension
    dim_hazmat = min(hazmat_score, 100)
    dim_energy = min(energy_score, 100)
    dim_defense = min(defense_score, 100)
    dim_transport = min(transport_score, 100)

    # Score composite pondere
    composite = int(
        dim_hazmat * 0.35 +
        dim_energy * 0.30 +
        dim_defense * 0.20 +
        dim_transport * 0.15
    )

    if composite < 20:
        level = "FAIBLE"
    elif composite < 50:
        level = "MODERE"
    elif composite < 75:
        level = "ELEVE"
    else:
        level = "CRITIQUE"

    return {
        "composite_risk_score": composite,
        "risk_level": level,
        "dimensions": {
            "hazmat_seveso": dim_hazmat,
            "energy_criticality": dim_energy,
            "defense_sovereignty": dim_defense,
            "transport_vulnerability": dim_transport
        },
        "critical_alerts_count": len(alerts),
        "alerts": alerts[:8]
    }
