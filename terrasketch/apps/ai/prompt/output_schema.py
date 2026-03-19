"""
Schéma JSON de sortie attendu de Claude pour la génération de plans paysagers.
"""

OUTPUT_SCHEMA = {
    "resume": "string — description synthétique du projet en 3-4 phrases",

    "zones": [
        {
            "id": "string — identifiant unique ex: zone_terrasse_1",
            "nom": "string — ex: Terrasse principale",
            "type": "terrasse|pelouse|massif|potager|allee|eau|cloture|autre",
            "surface_m2": "float",
            "position": {
                "x_pct": "float — % depuis bord gauche de la bbox parcelle (0-100)",
                "y_pct": "float — % depuis bord haut (0-100)",
                "largeur_pct": "float",
                "hauteur_pct": "float"
            },
            "description": "string",
            "materiau": "string|null — pour terrasses et allées uniquement"
        }
    ],

    "plantes": [
        {
            "name_latin": "string — DOIT être dans la liste plantes_disponibles",
            "name_common": "string",
            "zone_id": "string — référence à zones[].id",
            "quantite": "integer",
            "taille_recommandee": "3L|5L|10L|15L|20L|stade",
            "espacement_m": "float",
            "position_dans_zone": "fond|mi-hauteur|bordure|isole|haie",
            "justification": "string — pourquoi ce choix pour ce terrain/style/climat"
        }
    ],

    "cheminements": [
        {
            "type": "allee_principale|allee_secondaire|pas_japonais|escalier",
            "materiau": "string",
            "largeur_m": "float",
            "longueur_estimee_m": "float",
            "trace": "string — description du tracé"
        }
    ],

    "terrassement": {
        "necessaire": "boolean",
        "type": "deblai|remblai|mixte|null",
        "volume_estime_m3": "float|null",
        "description": "string"
    },

    "budget": {
        "total_estime_ht": "float",
        "phases": [
            {
                "numero": "integer",
                "nom": "string",
                "travaux": ["string"],
                "cout_estime_ht": "float",
                "duree_semaines": "integer",
                "periode_ideale": "string — ex: printemps année 1"
            }
        ]
    },

    "calendrier_entretien": {
        "janvier": ["string"],
        "fevrier": ["string"],
        "mars": ["string"],
        "avril": ["string"],
        "mai": ["string"],
        "juin": ["string"],
        "juillet": ["string"],
        "aout": ["string"],
        "septembre": ["string"],
        "octobre": ["string"],
        "novembre": ["string"],
        "decembre": ["string"]
    },

    "simulation_temporelle": {
        "j3_mois": "string — description aspect visuel à 3 mois",
        "j6_mois": "string",
        "j12_mois": "string",
        "j24_mois": "string",
        "j5_ans": "string"
    },

    "conseils_specifiques": [
        "string — conseil lié aux contraintes particulières du terrain"
    ]
}