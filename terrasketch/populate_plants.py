#!/usr/bin/env python
"""
Populate la base de données avec des plantes essentielles pour le MVP
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.plants.models import Plant, PlantFamily

def create_plant_families():
    """Créer les familles de plantes"""
    families = [
        {"name_fr": "Érabales", "name_latin": "Aceraceae"},
        {"name_fr": "Oléacées", "name_latin": "Oleaceae"},  
        {"name_fr": "Bétulacées", "name_latin": "Betulaceae"},
        {"name_fr": "Lamiacées", "name_latin": "Lamiaceae"},
        {"name_fr": "Hydrangéacées", "name_latin": "Hydrangeaceae"},
        {"name_fr": "Buxacées", "name_latin": "Buxaceae"},
        {"name_fr": "Paeoniacées", "name_latin": "Paeoniaceae"},
        {"name_fr": "Onagracées", "name_latin": "Onagraceae"},
        {"name_fr": "Renonculacées", "name_latin": "Ranunculaceae"},
        {"name_fr": "Aracées", "name_latin": "Araceae"},
        {"name_fr": "Palmiers", "name_latin": "Arecaceae"},
        {"name_fr": "Hibiscus", "name_latin": "Malvaceae"},
    ]
    
    created_families = {}
    for family_data in families:
        family, created = PlantFamily.objects.get_or_create(
            name_latin=family_data["name_latin"],
            defaults=family_data
        )
        created_families[family_data["name_latin"]] = family
        print(f"{'✅ Créé' if created else '🔄 Existe'}: {family.name_fr}")
    
    return created_families

def create_essential_plants(plant_families):
    """Créer les plantes essentielles pour chaque zone climatique française"""
    
    plants_data = [
        # ARBRES
        {
            "name_common_fr": "Érable du Japon",
            "name_latin": "Acer palmatum",
            "family": plant_families["Aceraceae"],
            "type": "tree",
            "climate_zones": ["Atlantique", "Continental", "Montagnard"],
            "height_adult_min_cm": 300,
            "height_adult_max_cm": 800,
            "width_adult_min_cm": 300,
            "width_adult_max_cm": 600,
            "water_need": "moderate",
            "sun_exposure": "partial_shade",
            "growth_rate": "slow",
            "foliage": "deciduous",
            "flowering_months": [3, 4],
            "flowering_color": "rouge",
            "frost_resistance_min_c": -15,
            "soil_preference": {"ph_min": 6.0, "ph_max": 7.0, "type": "acide"},
            "is_drought_resistant": False,
            "attracts_pollinators": False,
            "is_invasive": False
        },
        {
            "name_common_fr": "Olivier",
            "name_latin": "Olea europaea",
            "family": plant_families["Oleaceae"],
            "type": "tree",
            "climate_zones": ["Méditerranéen", "Tropical"],
            "height_adult_min_cm": 300,
            "height_adult_max_cm": 1000,
            "width_adult_min_cm": 300,
            "width_adult_max_cm": 800,
            "water_need": "low",
            "sun_exposure": "full_sun",
            "growth_rate": "slow",
            "foliage": "evergreen",
            "flowering_months": [4, 5],
            "flowering_color": "blanc",
            "frost_resistance_min_c": -10,
            "soil_preference": {"ph_min": 6.5, "ph_max": 8.0, "type": "calcaire"},
            "is_drought_resistant": True,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        {
            "name_common_fr": "Bouleau",
            "name_latin": "Betula pendula",
            "family": plant_families["Betulaceae"],
            "type": "tree",
            "climate_zones": ["Atlantique", "Continental", "Montagnard"],
            "height_adult_min_cm": 800,
            "height_adult_max_cm": 2000,
            "width_adult_min_cm": 400,
            "width_adult_max_cm": 800,
            "water_need": "moderate",
            "sun_exposure": "full_sun",
            "growth_rate": "fast",
            "foliage": "deciduous",
            "flowering_months": [3, 4],
            "flowering_color": "jaune",
            "frost_resistance_min_c": -25,
            "soil_preference": {"ph_min": 5.5, "ph_max": 7.0, "type": "neutre"},
            "is_drought_resistant": False,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        
        # ARBUSTES
        {
            "name_common_fr": "Lavande",
            "name_latin": "Lavandula angustifolia",
            "family": plant_families["Lamiaceae"],
            "type": "shrub",
            "climate_zones": ["Méditerranéen", "Atlantique"],
            "height_adult_min_cm": 50,
            "height_adult_max_cm": 100,
            "width_adult_min_cm": 80,
            "width_adult_max_cm": 120,
            "water_need": "low",
            "sun_exposure": "full_sun",
            "growth_rate": "moderate",
            "foliage": "evergreen",
            "flowering_months": [6, 7, 8],
            "flowering_color": "violet",
            "frost_resistance_min_c": -15,
            "soil_preference": {"ph_min": 6.5, "ph_max": 8.0, "type": "calcaire"},
            "is_drought_resistant": True,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        {
            "name_common_fr": "Hortensia",
            "name_latin": "Hydrangea macrophylla",
            "family": plant_families["Hydrangeaceae"],
            "type": "shrub",
            "climate_zones": ["Atlantique", "Continental"],
            "height_adult_min_cm": 100,
            "height_adult_max_cm": 200,
            "width_adult_min_cm": 100,
            "width_adult_max_cm": 200,
            "water_need": "high",
            "sun_exposure": "partial_shade",
            "growth_rate": "moderate",
            "foliage": "deciduous",
            "flowering_months": [6, 7, 8, 9],
            "flowering_color": "bleu,rose",
            "frost_resistance_min_c": -15,
            "soil_preference": {"ph_min": 5.0, "ph_max": 7.0, "type": "acide"},
            "is_drought_resistant": False,
            "attracts_pollinators": False,
            "is_invasive": False
        },
        {
            "name_common_fr": "Buis",
            "name_latin": "Buxus sempervirens",
            "family": plant_families["Buxaceae"],
            "type": "shrub",
            "climate_zones": ["Atlantique", "Continental", "Méditerranéen"],
            "height_adult_min_cm": 50,
            "height_adult_max_cm": 300,
            "width_adult_min_cm": 50,
            "width_adult_max_cm": 200,
            "water_need": "moderate",
            "sun_exposure": "partial_shade",
            "growth_rate": "slow",
            "foliage": "evergreen",
            "flowering_months": [3, 4],
            "flowering_color": "vert",
            "frost_resistance_min_c": -15,
            "soil_preference": {"ph_min": 6.0, "ph_max": 8.0, "type": "neutre"},
            "is_drought_resistant": False,
            "attracts_pollinators": False,
            "is_invasive": False
        },
        
        # VIVACES
        {
            "name_common_fr": "Pivoine",
            "name_latin": "Paeonia lactiflora",
            "family": plant_families["Paeoniaceae"],
            "type": "perennial",
            "climate_zones": ["Atlantique", "Continental", "Montagnard"],
            "height_adult_min_cm": 60,
            "height_adult_max_cm": 100,
            "width_adult_min_cm": 60,
            "width_adult_max_cm": 80,
            "water_need": "moderate",
            "sun_exposure": "full_sun",
            "growth_rate": "slow",
            "foliage": "deciduous",
            "flowering_months": [5, 6],
            "flowering_color": "rose,blanc",
            "frost_resistance_min_c": -25,
            "soil_preference": {"ph_min": 6.0, "ph_max": 7.5, "type": "neutre"},
            "is_drought_resistant": False,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        {
            "name_common_fr": "Gaura",
            "name_latin": "Gaura lindheimeri",
            "family": plant_families["Onagraceae"],
            "type": "perennial",
            "climate_zones": ["Atlantique", "Méditerranéen"],
            "height_adult_min_cm": 80,
            "height_adult_max_cm": 120,
            "width_adult_min_cm": 60,
            "width_adult_max_cm": 100,
            "water_need": "low",
            "sun_exposure": "full_sun",
            "growth_rate": "fast",
            "foliage": "deciduous",
            "flowering_months": [6, 7, 8, 9],
            "flowering_color": "blanc,rose",
            "frost_resistance_min_c": -10,
            "soil_preference": {"ph_min": 6.0, "ph_max": 8.0, "type": "neutre"},
            "is_drought_resistant": True,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        
        # GRIMPANTES
        {
            "name_common_fr": "Clématite",
            "name_latin": "Clematis montana",
            "family": plant_families["Ranunculaceae"],
            "type": "climber",
            "climate_zones": ["Atlantique", "Continental"],
            "height_adult_min_cm": 300,
            "height_adult_max_cm": 800,
            "width_adult_min_cm": 200,
            "width_adult_max_cm": 400,
            "water_need": "moderate",
            "sun_exposure": "partial_shade",
            "growth_rate": "fast",
            "foliage": "deciduous",
            "flowering_months": [5, 6],
            "flowering_color": "blanc,rose",
            "frost_resistance_min_c": -15,
            "soil_preference": {"ph_min": 6.0, "ph_max": 7.5, "type": "neutre"},
            "is_drought_resistant": False,
            "attracts_pollinators": True,
            "is_invasive": False
        },
        
        # PLANTES TROPICALES
        {
            "name_common_fr": "Monstera",
            "name_latin": "Monstera deliciosa",
            "family": plant_families["Araceae"],
            "type": "perennial",
            "climate_zones": ["Tropical"],
            "height_adult_min_cm": 200,
            "height_adult_max_cm": 500,
            "width_adult_min_cm": 150,
            "width_adult_max_cm": 300,
            "water_need": "high",
            "sun_exposure": "partial_shade",
            "growth_rate": "fast",
            "foliage": "evergreen",
            "flowering_months": [],
            "flowering_color": "",
            "frost_resistance_min_c": 10,
            "soil_preference": {"ph_min": 5.5, "ph_max": 7.0, "type": "humifère"},
            "is_drought_resistant": False,
            "attracts_pollinators": False,
            "is_invasive": False
        },
        {
            "name_common_fr": "Palmier Phoenix",
            "name_latin": "Phoenix canariensis",
            "family": plant_families["Arecaceae"],
            "type": "tree",
            "climate_zones": ["Tropical", "Méditerranéen"],
            "height_adult_min_cm": 800,
            "height_adult_max_cm": 1800,
            "width_adult_min_cm": 600,
            "width_adult_max_cm": 1000,
            "water_need": "moderate",
            "sun_exposure": "full_sun",
            "growth_rate": "slow",
            "foliage": "evergreen",
            "flowering_months": [3, 4, 5],
            "flowering_color": "jaune",
            "frost_resistance_min_c": -5,
            "soil_preference": {"ph_min": 6.0, "ph_max": 8.0, "type": "sableux"},
            "is_drought_resistant": True,
            "attracts_pollinators": False,
            "is_invasive": False
        },
        {
            "name_common_fr": "Hibiscus tropical",
            "name_latin": "Hibiscus rosa-sinensis",
            "family": plant_families["Malvaceae"],
            "type": "shrub",
            "climate_zones": ["Tropical"],
            "height_adult_min_cm": 150,
            "height_adult_max_cm": 400,
            "width_adult_min_cm": 150,
            "width_adult_max_cm": 300,
            "water_need": "high",
            "sun_exposure": "full_sun",
            "growth_rate": "fast",
            "foliage": "evergreen",
            "flowering_months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "flowering_color": "rouge,rose,jaune",
            "frost_resistance_min_c": 5,
            "soil_preference": {"ph_min": 6.0, "ph_max": 7.5, "type": "humifère"},
            "is_drought_resistant": False,
            "attracts_pollinators": True,
            "is_invasive": False
        }
    ]
    
    created_count = 0
    for plant_data in plants_data:        
        plant, created = Plant.objects.get_or_create(
            name_latin=plant_data["name_latin"],
            defaults=plant_data
        )
        
        if created:
            created_count += 1
            print(f"✅ Créé: {plant.name_common_fr} ({plant.name_latin})")
        else:
            print(f"🔄 Existe: {plant.name_common_fr}")
    
    return created_count

def main():
    print("🌱 Populate Base de Données Plantes TerraSketch")
    print("="*50)
    
    # Créer les familles
    print("\n📂 Création familles de plantes...")
    plant_families = create_plant_families()
    
    # Créer les plantes
    print(f"\n🌿 Création plantes...")
    plant_count = create_essential_plants(plant_families)
    
    # Statistiques finales
    total_families = PlantFamily.objects.count()
    total_plants = Plant.objects.count()
    
    print(f"\n📊 Résumé:")
    print(f"✅ Familles: {total_families}")
    print(f"✅ Plantes: {total_plants} ({plant_count} nouvelles)")
    
    # Répartition par zone climatique
    print(f"\n🌍 Répartition par zone:")
    zones = ["Atlantique", "Continental", "Méditerranéen", "Montagnard", "Tropical"]
    for zone in zones:
        # Version compatible SQLite - compter en Python
        count = sum(1 for plant in Plant.objects.all() if zone in plant.climate_zones)
        print(f"  {zone}: {count} espèces")
    
    print(f"\n🎉 Base de données plantes prête pour le MVP!")
    print(f"▶️  Compatible avec le système IA de TerraSketch")

if __name__ == "__main__":
    main()