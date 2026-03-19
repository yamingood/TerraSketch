"""
Validateurs pour les réponses JSON retournées par Claude.
"""
import json
import re
from typing import Dict, List, Tuple


class PlanParseError(Exception):
    """Exception levée lors d'erreurs de parsing du plan."""
    pass


def validate_plan_response(response_json: dict, context: dict) -> Tuple[bool, List[str]]:
    """
    Valide la réponse JSON retournée par Claude.

    Vérifications structurelles :
    1. Tous les champs obligatoires présents (zones, plantes, budget, etc.)
    2. Chaque zone a un id unique
    3. Chaque plante référence un zone_id existant
    4. Chaque plante est dans la liste des plantes_disponibles du contexte

    Vérifications métier :
    5. Somme surfaces zones ≈ surface_m2 parcelle (±20% tolérance)
    6. Budget total_estime_ht dans la fourchette ±30% du budget_preferences
    7. Somme des coûts phases ≈ budget total (±5%)
    8. Au moins une plante par zone de type massif/pelouse
    9. Calendrier entretien : 12 mois présents

    Retourne (is_valid: bool, errors: list[str])
    Si is_valid=False, le générateur peut retry une fois (max 2 tentatives).
    """
    errors = []
    
    # 1. Vérifications structurelles
    errors.extend(_check_required_fields(response_json))
    
    # 2. Vérifier l'unicité des IDs de zones
    errors.extend(_check_zone_ids_unique(response_json))
    
    # 3. Vérifier les références zone_id des plantes
    errors.extend(_check_plant_zone_references(response_json))
    
    # 4. Vérifier que les plantes sont dans la liste disponible
    errors.extend(_check_plants_in_available_list(response_json, context))
    
    # 5. Vérifier la cohérence des surfaces
    errors.extend(_check_surface_consistency(response_json, context))
    
    # 6. Vérifier la cohérence budgétaire
    errors.extend(_check_budget_consistency(response_json, context))
    
    # 7. Vérifier le budget des phases
    errors.extend(_check_phase_budget_consistency(response_json))
    
    # 8. Vérifier qu'il y a des plantes dans les zones végétales
    errors.extend(_check_plants_in_vegetation_zones(response_json))
    
    # 9. Vérifier le calendrier d'entretien
    errors.extend(_check_maintenance_calendar(response_json))
    
    return len(errors) == 0, errors


def _check_required_fields(response_json: dict) -> List[str]:
    """Vérifie la présence des champs obligatoires."""
    errors = []
    required_fields = [
        'resume', 'zones', 'plantes', 'cheminements', 'terrassement',
        'budget', 'calendrier_entretien', 'simulation_temporelle', 'conseils_specifiques'
    ]
    
    for field in required_fields:
        if field not in response_json:
            errors.append(f"Champ obligatoire manquant : {field}")
    
    # Vérifications spécifiques pour les champs complexes
    if 'zones' in response_json:
        if not isinstance(response_json['zones'], list) or len(response_json['zones']) == 0:
            errors.append("Au moins une zone doit être définie")
    
    if 'budget' in response_json:
        budget = response_json['budget']
        if not isinstance(budget, dict):
            errors.append("Le budget doit être un objet")
        else:
            if 'total_estime_ht' not in budget:
                errors.append("budget.total_estime_ht manquant")
            if 'phases' not in budget or not isinstance(budget['phases'], list):
                errors.append("budget.phases manquant ou invalide")
    
    return errors


def _check_zone_ids_unique(response_json: dict) -> List[str]:
    """Vérifie que les IDs de zones sont uniques."""
    errors = []
    
    if 'zones' not in response_json:
        return errors
    
    zone_ids = []
    for i, zone in enumerate(response_json['zones']):
        if not isinstance(zone, dict):
            errors.append(f"Zone {i} n'est pas un objet valide")
            continue
            
        if 'id' not in zone:
            errors.append(f"Zone {i} n'a pas d'ID")
            continue
            
        zone_id = zone['id']
        if zone_id in zone_ids:
            errors.append(f"ID de zone dupliqué : {zone_id}")
        else:
            zone_ids.append(zone_id)
    
    return errors


def _check_plant_zone_references(response_json: dict) -> List[str]:
    """Vérifie que les plantes référencent des zones existantes."""
    errors = []
    
    if 'zones' not in response_json or 'plantes' not in response_json:
        return errors
    
    # Collecter les IDs de zones valides
    zone_ids = set()
    for zone in response_json['zones']:
        if isinstance(zone, dict) and 'id' in zone:
            zone_ids.add(zone['id'])
    
    # Vérifier les références des plantes
    for i, plant in enumerate(response_json['plantes']):
        if not isinstance(plant, dict):
            continue
            
        if 'zone_id' not in plant:
            errors.append(f"Plante {i} n'a pas de zone_id")
            continue
            
        zone_id = plant['zone_id']
        if zone_id not in zone_ids:
            errors.append(f"Plante {i} référence une zone inexistante : {zone_id}")
    
    return errors


def _check_plants_in_available_list(response_json: dict, context: dict) -> List[str]:
    """Vérifie que toutes les plantes sont dans la liste disponible."""
    errors = []
    
    if 'plantes' not in response_json:
        return errors
    
    available_plants = context.get('plantes_disponibles', [])
    if not available_plants:
        return errors  # Pas de liste de référence
    
    # Créer un ensemble des noms latins disponibles
    available_latin_names = set()
    for plant in available_plants:
        if isinstance(plant, dict) and 'name_latin' in plant:
            available_latin_names.add(plant['name_latin'].lower().strip())
    
    # Vérifier chaque plante utilisée
    for i, plant in enumerate(response_json['plantes']):
        if not isinstance(plant, dict) or 'name_latin' not in plant:
            continue
            
        plant_latin = plant['name_latin'].lower().strip()
        if plant_latin not in available_latin_names:
            plant_name = plant.get('name_common', plant['name_latin'])
            errors.append(f"Plante non autorisée : {plant_name} ({plant['name_latin']})")
    
    return errors


def _check_surface_consistency(response_json: dict, context: dict) -> List[str]:
    """Vérifie la cohérence des surfaces."""
    errors = []
    
    if 'zones' not in response_json:
        return errors
    
    parcelle_surface = context.get('parcelle', {}).get('surface_m2', 0)
    if parcelle_surface <= 0:
        return errors  # Pas de surface de référence
    
    # Calculer la somme des surfaces des zones
    total_zone_surface = 0
    for zone in response_json['zones']:
        if isinstance(zone, dict) and 'surface_m2' in zone:
            try:
                surface = float(zone['surface_m2'])
                total_zone_surface += surface
            except (ValueError, TypeError):
                errors.append(f"Surface invalide pour zone {zone.get('id', 'unknown')}")
    
    # Vérifier la tolérance (±20%)
    tolerance = 0.2
    min_expected = parcelle_surface * (1 - tolerance)
    max_expected = parcelle_surface * (1 + tolerance)
    
    if total_zone_surface < min_expected or total_zone_surface > max_expected:
        errors.append(
            f"Somme des surfaces zones ({total_zone_surface:.1f}m²) "
            f"ne correspond pas à la parcelle ({parcelle_surface:.1f}m²)"
        )
    
    return errors


def _check_budget_consistency(response_json: dict, context: dict) -> List[str]:
    """Vérifie la cohérence budgétaire avec les préférences."""
    errors = []
    
    if 'budget' not in response_json:
        return errors
    
    budget_data = response_json['budget']
    if not isinstance(budget_data, dict) or 'total_estime_ht' not in budget_data:
        return errors
    
    try:
        estimated_budget = float(budget_data['total_estime_ht'])
    except (ValueError, TypeError):
        errors.append("Budget total invalide")
        return errors
    
    # Récupérer le budget préféré
    preferences = context.get('preferences', {})
    preferred_budget = preferences.get('budget_total_ht', 0)
    
    if preferred_budget > 0:
        # Vérifier la tolérance (±30%)
        tolerance = 0.3
        min_expected = preferred_budget * (1 - tolerance)
        max_expected = preferred_budget * (1 + tolerance)
        
        if estimated_budget < min_expected or estimated_budget > max_expected:
            errors.append(
                f"Budget estimé ({estimated_budget:.0f}€) "
                f"s'écarte trop du budget souhaité ({preferred_budget:.0f}€)"
            )
    
    return errors


def _check_phase_budget_consistency(response_json: dict) -> List[str]:
    """Vérifie que la somme des budgets de phases correspond au total."""
    errors = []
    
    if 'budget' not in response_json:
        return errors
    
    budget_data = response_json['budget']
    if not isinstance(budget_data, dict):
        return errors
    
    try:
        total_budget = float(budget_data.get('total_estime_ht', 0))
    except (ValueError, TypeError):
        return errors
    
    phases = budget_data.get('phases', [])
    if not isinstance(phases, list) or len(phases) == 0:
        return errors
    
    # Calculer la somme des phases
    phases_sum = 0
    for phase in phases:
        if isinstance(phase, dict) and 'cout_estime_ht' in phase:
            try:
                phase_cost = float(phase['cout_estime_ht'])
                phases_sum += phase_cost
            except (ValueError, TypeError):
                errors.append(f"Coût invalide pour phase {phase.get('numero', 'unknown')}")
    
    # Vérifier la tolérance (±5%)
    if total_budget > 0:
        tolerance = 0.05
        min_expected = total_budget * (1 - tolerance)
        max_expected = total_budget * (1 + tolerance)
        
        if phases_sum < min_expected or phases_sum > max_expected:
            errors.append(
                f"Somme phases ({phases_sum:.0f}€) "
                f"ne correspond pas au total ({total_budget:.0f}€)"
            )
    
    return errors


def _check_plants_in_vegetation_zones(response_json: dict) -> List[str]:
    """Vérifie qu'il y a des plantes dans les zones végétales."""
    errors = []
    
    if 'zones' not in response_json or 'plantes' not in response_json:
        return errors
    
    # Identifier les zones végétales
    vegetation_zones = set()
    for zone in response_json['zones']:
        if isinstance(zone, dict) and 'type' in zone and 'id' in zone:
            zone_type = zone['type']
            if zone_type in ['massif', 'pelouse', 'potager']:
                vegetation_zones.add(zone['id'])
    
    # Vérifier qu'il y a des plantes dans ces zones
    planted_zones = set()
    for plant in response_json['plantes']:
        if isinstance(plant, dict) and 'zone_id' in plant:
            planted_zones.add(plant['zone_id'])
    
    # Zones végétales sans plantes
    unplanted_vegetation = vegetation_zones - planted_zones
    for zone_id in unplanted_vegetation:
        errors.append(f"Zone végétale {zone_id} n'a pas de plantes")
    
    return errors


def _check_maintenance_calendar(response_json: dict) -> List[str]:
    """Vérifie que le calendrier d'entretien a 12 mois."""
    errors = []
    
    if 'calendrier_entretien' not in response_json:
        return errors
    
    calendar = response_json['calendrier_entretien']
    if not isinstance(calendar, dict):
        errors.append("Calendrier d'entretien invalide")
        return errors
    
    expected_months = [
        'janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre'
    ]
    
    for month in expected_months:
        if month not in calendar:
            errors.append(f"Mois manquant dans le calendrier : {month}")
    
    return errors


def extract_json_from_response(raw_response: str) -> dict:
    """
    Extrait et parse le JSON depuis la réponse brute de Claude.

    Gère les cas pathologiques où Claude aurait quand même ajouté :
    - Des backticks markdown (```json ... ```)
    - Du texte avant/après le JSON
    - Des trailing commas (JSON non strict)

    Stratégie :
    1. Tenter json.loads() direct
    2. Si échec : regex pour extraire le bloc JSON entre { et }
    3. Si échec : lever PlanParseError
    """
    if not raw_response or not raw_response.strip():
        raise PlanParseError("Réponse vide")
    
    # Nettoyer la réponse
    cleaned = raw_response.strip()
    
    # 1. Tentative directe
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 2. Supprimer les balises markdown si présentes
    cleaned = re.sub(r'```json\s*', '', cleaned)
    cleaned = re.sub(r'\s*```', '', cleaned)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 3. Extraire le premier objet JSON trouvé
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        json_content = json_match.group(0)
        
        # Réparer les erreurs courantes avant parsing
        json_content = repair_common_errors(json_content)
        
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            raise PlanParseError(f"JSON invalide après réparation : {str(e)}")
    
    raise PlanParseError("Aucun JSON valide trouvé dans la réponse")


def repair_common_errors(raw_response: str) -> str:
    """
    Tente de corriger les erreurs JSON courantes avant parsing :
    - Trailing commas avant } ou ]
    - Guillemets simples au lieu de doubles
    - Valeurs null non quotées mal écrites
    """
    repaired = raw_response
    
    # 1. Supprimer les trailing commas
    repaired = re.sub(r',\s*}', '}', repaired)
    repaired = re.sub(r',\s*]', ']', repaired)
    
    # 2. Remplacer les guillemets simples par des doubles (seulement autour des clés)
    # Attention à ne pas affecter les guillemets dans les valeurs
    repaired = re.sub(r"'([^']+)':", r'"\1":', repaired)
    
    # 3. Corriger les valeurs null mal écrites
    repaired = re.sub(r':\s*null\b', ': null', repaired)
    repaired = re.sub(r':\s*true\b', ': true', repaired)
    repaired = re.sub(r':\s*false\b', ': false', repaired)
    
    return repaired