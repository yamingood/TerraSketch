"""
Constructeur de prompt principal pour Claude.

Transforme le contexte assemblé en prompt structuré XML prêt à être envoyé à l'API.
"""
import json
from typing import Dict, List
from .output_schema import OUTPUT_SCHEMA
from django.conf import settings


def build_landscape_prompt(context: dict) -> str:
    """
    Construit le prompt utilisateur complet à partir du contexte assemblé.

    Le prompt est structuré en 4 sections XML :
    1. <context>    — toutes les données terrain, climat, préférences
    2. <plantes_disponibles>  — liste filtrée des plantes compatibles
    3. <instructions>         — directives de génération
    4. <output_schema>        — schéma JSON attendu en sortie

    Paramètre context : dict retourné par context_assembler.assemble_project_context()
    Retourne : string (le prompt complet)
    """
    # Construire les sections du prompt
    terrain_section = _build_terrain_section(context)
    climat_section = _build_climat_section(context)
    preferences_section = _build_preferences_section(context.get('preferences', {}))
    plants_section = _build_plants_section(context.get('plantes_disponibles', []))
    instructions_section = _build_instructions_section(
        context.get('preferences', {}),
        context.get('parcelle', {}).get('surface_m2', 0)
    )
    output_schema_section = _build_output_schema_section()
    
    # Assembler le prompt final
    prompt = f"""
{terrain_section}

{climat_section}

{preferences_section}

{plants_section}

{instructions_section}

{output_schema_section}
"""
    
    return prompt.strip()


def _build_terrain_section(context: dict) -> str:
    """
    Construit la section <terrain> du prompt.
    """
    parcelle = context.get('parcelle', {})
    solaire = context.get('solaire', {})
    terrassement = context.get('terrassement', {})
    
    terrain_xml = f"""<terrain>
  <surface_m2>{parcelle.get('surface_m2', 0)}</surface_m2>
  <commune>{_get_commune_display(context)}</commune>
  <zone_climatique>{context.get('zones', {}).get('zone_climatique', 'Continental')}</zone_climatique>
  <zone_rusticite>{context.get('zones', {}).get('zone_rusticite', 'Z8a')}</zone_rusticite>
  <orientation_principale>{solaire.get('orientation_principale', 'sud-ouest')}</orientation_principale>
  <ensoleillement>{solaire.get('ensoleillement', 'moyen')}</ensoleillement>
  <heures_soleil_ete>{solaire.get('heures_soleil_ete', 12.0)}</heures_soleil_ete>
  <denivele_m>{terrassement.get('denivele_estime_m', 1.0)}</denivele_m>
  <pente_moyenne_pct>{terrassement.get('pente_moyenne_pct', 2.0)}</pente_moyenne_pct>
  <terrassement_complexite>{terrassement.get('complexite', 'moyenne')}</terrassement_complexite>
</terrain>"""
    
    return terrain_xml


def _get_commune_display(context: dict) -> str:
    """
    Formate l'affichage de la commune.
    """
    climat = context.get('climat', {})
    commune = climat.get('commune', 'France')
    
    # Ajouter le département si possible (estimation basée sur la zone)
    zone_climatique = context.get('zones', {}).get('zone_climatique', '')
    
    if zone_climatique == "Méditerranéen":
        return f"{commune} (Sud de la France)"
    elif zone_climatique == "Atlantique":
        return f"{commune} (Côte Atlantique)"
    elif zone_climatique == "Montagnard":
        return f"{commune} (Région montagneuse)"
    else:
        return f"{commune} (France)"


def _build_climat_section(context: dict) -> str:
    """
    Construit la section <climat> du prompt.
    """
    climat = context.get('climat', {})
    stress_hydrique = context.get('zones', {}).get('stress_hydrique', 'modere')
    
    climat_xml = f"""<climat>
  <temperature_moy_annuelle>{climat.get('temperature_moy_annuelle', 12.0)}°C</temperature_moy_annuelle>
  <temperature_minimale_record>{climat.get('temperature_minimale_record', -7.0)}°C</temperature_minimale_record>
  <precipitations_annuelles>{climat.get('precipitations_annuelles', 800)}mm</precipitations_annuelles>
  <jours_gel_par_an>{climat.get('jours_gel_par_an', 20)}</jours_gel_par_an>
  <stress_hydrique>{stress_hydrique}</stress_hydrique>
</climat>"""
    
    return climat_xml


def _build_preferences_section(preferences: dict) -> str:
    """
    Construit la section <preferences> du prompt.
    """
    # Extraire et formatter les préférences
    style = preferences.get('style', 'contemporain')
    ambiance = preferences.get('ambiance', '')
    usages = preferences.get('usages', '')
    terrasse_m2 = preferences.get('superficie_terrasse_souhaitee_m2', 20)
    budget = preferences.get('budget_total_ht', 10000)
    phases = preferences.get('nombre_phases', 1)
    entretien = preferences.get('niveau_entretien', 'moyen')
    
    # Construire la section contraintes
    contraintes_xml = ""
    if preferences.get('enfants'):
        contraintes_xml += "    <enfants>oui</enfants>\n"
    if preferences.get('animaux'):
        contraintes_xml += f"    <animaux>{preferences.get('animaux', 'oui')}</animaux>\n"
    
    # Plantes souhaitées
    plantes_souhaitees = preferences.get('plantes_souhaitees', [])
    if isinstance(plantes_souhaitees, list):
        plantes_str = ", ".join(plantes_souhaitees)
    else:
        plantes_str = str(plantes_souhaitees)
    
    # Fruitiers
    fruitiers = "oui" if preferences.get('fruitiers') else "non"
    
    preferences_xml = f"""<preferences>
  <style>{style}</style>
  <ambiance>{ambiance}</ambiance>
  <usages>{usages}</usages>
  <superficie_terrasse_souhaitee_m2>{terrasse_m2}</superficie_terrasse_souhaitee_m2>
  <budget_total_ht>{budget}</budget_total_ht>
  <nombre_phases>{phases}</nombre_phases>
  <niveau_entretien>{entretien}</niveau_entretien>
  <contraintes>
{contraintes_xml.rstrip()}
  </contraintes>
  <plantes_souhaitees>{plantes_str}</plantes_souhaitees>
  <fruitiers>{fruitiers}</fruitiers>
</preferences>"""
    
    return preferences_xml


def _build_plants_section(plants: list) -> str:
    """
    Construit la section <plantes_disponibles>.

    Format compact pour minimiser les tokens tout en gardant les infos clés.
    Chaque plante sur ~3 lignes XML.
    """
    if not plants:
        return """<plantes_disponibles>
  <note>ATTENTION : Tu DOIS utiliser uniquement les plantes de cette liste dans ta réponse JSON.</note>
  <plante>Aucune plante disponible</plante>
</plantes_disponibles>"""
    
    plants_xml = """<plantes_disponibles>
  <note>ATTENTION : Tu DOIS utiliser uniquement les plantes de cette liste dans ta réponse JSON.</note>"""
    
    for plant in plants:
        # Format compact : nom latin, nom commun, catégorie, taille, exposition, entretien
        name_latin = plant.get('name_latin', '')
        name_common = plant.get('name_common', '')
        category = plant.get('category', 'Autre')
        height_cm = plant.get('height_max', 100)
        sun_req = plant.get('sun_requirement', 'soleil')
        maintenance = plant.get('maintenance_level', 'moyen')
        
        plants_xml += f"""
  <plante>
    <nom_latin>{name_latin}</nom_latin>
    <nom_commun>{name_common}</nom_commun>
    <categorie>{category}</categorie>
    <hauteur_max_cm>{height_cm}</hauteur_max_cm>
    <exposition>{sun_req}</exposition>
    <entretien>{maintenance}</entretien>
  </plante>"""
    
    plants_xml += "\n</plantes_disponibles>"
    
    return plants_xml


def _build_instructions_section(preferences: dict, surface_m2: float) -> str:
    """
    Construit la section <instructions> avec les directives de génération.
    """
    # Instructions de base
    instructions_base = f"""<instructions>
  <directives_principales>
    - Couvrir 100% de la surface ({surface_m2}m²) avec des zones (somme surfaces zones ≈ {surface_m2}m²)
    - Respecter le budget total ±10% de tolérance
    - Proposer uniquement des plantes de la liste &lt;plantes_disponibles&gt;
    - Adapter le style et l'ambiance aux préférences utilisateur
    - Tenir compte de l'orientation solaire pour placer les zones
    - Ne pas dépasser le budget par phase
    - Calendrier entretien adapté à la zone climatique française
  </directives_principales>"""
    
    # Instructions conditionnelles
    conditional_instructions = []
    
    if surface_m2 < 80:
        conditional_instructions.append("Surface < 80m² : pas de pelouse grande taille, privilégier les massifs compacts")
    
    if surface_m2 > 500:
        conditional_instructions.append("Surface > 500m² : prévoir au moins 3 zones distinctes")
    
    if preferences.get('enfants'):
        conditional_instructions.append("Enfants présents : inclure zone de jeux, éviter plantes épineuses et toxiques")
    
    budget = preferences.get('budget_total_ht', 10000)
    if budget > 30000:
        conditional_instructions.append("Budget élevé : possibilité d'aménagements sophistiqués (bassin, pergola, éclairage)")
    elif budget < 5000:
        conditional_instructions.append("Budget serré : privilégier les plantations, minimiser les aménagements coûteux")
    
    entretien = preferences.get('niveau_entretien', 'moyen')
    if entretien == 'faible':
        conditional_instructions.append("Entretien faible souhaité : privilégier vivaces et arbustes persistants, éviter plantes gourmandes en taille")
    
    # Ajouter les instructions conditionnelles
    if conditional_instructions:
        instructions_base += "\n  <directives_conditionnelles>\n"
        for instruction in conditional_instructions:
            instructions_base += f"    - {instruction}\n"
        instructions_base += "  </directives_conditionnelles>"
    
    instructions_base += "\n</instructions>"
    
    return instructions_base


def _build_output_schema_section() -> str:
    """
    Sérialise OUTPUT_SCHEMA en JSON et l'injecte dans le prompt.
    """
    schema_json = json.dumps(OUTPUT_SCHEMA, indent=2, ensure_ascii=False)
    
    output_section = f"""<output_schema>
  <format>
    Répondre UNIQUEMENT avec le JSON suivant :
    - Pas de texte avant ni après le JSON
    - Pas de balises ```json
    - JSON valide et parseable
    - Tous les champs obligatoires remplis
  </format>
  
  <schema>
{schema_json}
  </schema>
</output_schema>"""
    
    return output_section


def estimate_prompt_tokens(prompt: str) -> int:
    """
    Estimation approximative du nombre de tokens.
    Règle : 1 token ≈ 4 caractères en français.
    Utile pour monitoring et éviter de dépasser le context window.
    """
    return len(prompt) // 4


def build_correction_prompt(original_prompt: str, plan_json: dict, errors: List[str]) -> str:
    """
    Construit un prompt de correction ciblé pour le retry.
    
    Structure :
    "Le plan généré contient les erreurs suivantes :
    - [error 1]
    - [error 2]

    Voici le plan à corriger : [plan_json]

    Génère un plan corrigé en JSON valide qui résout ces erreurs.
    Conserve la structure générale du plan, corrige uniquement les erreurs."
    """
    errors_text = "\n".join([f"- {error}" for error in errors])
    plan_text = json.dumps(plan_json, indent=2, ensure_ascii=False)
    
    correction_prompt = f"""Le plan généré contient les erreurs suivantes :
{errors_text}

Voici le plan à corriger :
{plan_text}

Génère un plan corrigé en JSON valide qui résout ces erreurs spécifiques.
Conserve la structure générale du plan, corrige uniquement les problèmes identifiés.
Assure-toi que :
- Toutes les plantes utilisées sont dans la liste plantes_disponibles fournie initialement
- Les surfaces des zones totalisent bien la surface de la parcelle
- Le budget total correspond à la somme des phases
- Tous les champs obligatoires sont présents

Réponds UNIQUEMENT avec le JSON corrigé, sans texte avant ni après."""
    
    return correction_prompt