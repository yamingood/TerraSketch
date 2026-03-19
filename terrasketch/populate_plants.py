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
            "name": "Olivier",
            "scientific_name": "Olea europaea", 
            "category": "arbres",
            "climate_zones": ["Méditerranéen", "Tropical"],
            "hardiness_zone": 8,
            "height_min": 3.0,
            "height_max": 10.0,
            "spread_min": 3.0,
            "spread_max": 8.0,
            "soil_ph_min": 6.5,
            "soil_ph_max": 8.0,
            "water_needs": "low",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "spring",
            "foliage_color": "green,silver",
            "is_native": True,
            "price_range": "high"
        },
        {
            "name": "Bouleau",
            "scientific_name": "Betula pendula",
            "category": "arbres", 
            "climate_zones": ["Atlantique", "Continental", "Montagnard"],
            "hardiness_zone": 3,
            "height_min": 8.0,
            "height_max": 20.0,
            "spread_min": 4.0,
            "spread_max": 8.0,
            "soil_ph_min": 5.5,
            "soil_ph_max": 7.0,
            "water_needs": "medium",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "spring",
            "foliage_color": "green,yellow",
            "is_native": True,
            "price_range": "medium"
        },
        
        # ARBUSTES
        {
            "name": "Lavande",
            "scientific_name": "Lavandula angustifolia",
            "category": "arbustes",
            "climate_zones": ["Méditerranéen", "Atlantique"],
            "hardiness_zone": 5,
            "height_min": 0.5,
            "height_max": 1.0,
            "spread_min": 0.8,
            "spread_max": 1.2,
            "soil_ph_min": 6.5,
            "soil_ph_max": 8.0,
            "water_needs": "low",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "summer",
            "foliage_color": "silver,green",
            "is_native": True,
            "price_range": "low"
        },
        {
            "name": "Hortensia",
            "scientific_name": "Hydrangea macrophylla",
            "category": "arbustes",
            "climate_zones": ["Atlantique", "Continental"],
            "hardiness_zone": 6,
            "height_min": 1.0,
            "height_max": 2.0,
            "spread_min": 1.0,
            "spread_max": 2.0,
            "soil_ph_min": 5.0,
            "soil_ph_max": 7.0,
            "water_needs": "high",
            "sun_exposure": "partial_shade",
            "maintenance_level": "medium",
            "bloom_period": "summer",
            "foliage_color": "green",
            "is_native": False,
            "price_range": "medium"
        },
        {
            "name": "Buis",
            "scientific_name": "Buxus sempervirens",
            "category": "arbustes",
            "climate_zones": ["Atlantique", "Continental", "Méditerranéen"],
            "hardiness_zone": 6,
            "height_min": 0.5,
            "height_max": 3.0,
            "spread_min": 0.5,
            "spread_max": 2.0,
            "soil_ph_min": 6.0,
            "soil_ph_max": 8.0,
            "water_needs": "medium",
            "sun_exposure": "partial_sun",
            "maintenance_level": "high",
            "bloom_period": "spring",
            "foliage_color": "green",
            "is_native": True,
            "price_range": "medium"
        },
        
        # VIVACES
        {
            "name": "Pivoine",
            "scientific_name": "Paeonia lactiflora",
            "category": "vivaces",
            "climate_zones": ["Atlantique", "Continental", "Montagnard"],
            "hardiness_zone": 3,
            "height_min": 0.6,
            "height_max": 1.0,
            "spread_min": 0.6,
            "spread_max": 0.8,
            "soil_ph_min": 6.0,
            "soil_ph_max": 7.5,
            "water_needs": "medium",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "late_spring",
            "foliage_color": "green",
            "is_native": False,
            "price_range": "high"
        },
        {
            "name": "Gaura",
            "scientific_name": "Gaura lindheimeri",
            "category": "vivaces",
            "climate_zones": ["Atlantique", "Méditerranéen"],
            "hardiness_zone": 6,
            "height_min": 0.8,
            "height_max": 1.2,
            "spread_min": 0.6,
            "spread_max": 1.0,
            "soil_ph_min": 6.0,
            "soil_ph_max": 8.0,
            "water_needs": "low",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "summer",
            "foliage_color": "green",
            "is_native": False,
            "price_range": "low"
        },
        
        # AROMATIQUES
        {
            "name": "Romarin",
            "scientific_name": "Rosmarinus officinalis",
            "category": "aromatiques",
            "climate_zones": ["Méditerranéen", "Atlantique"],
            "hardiness_zone": 7,
            "height_min": 0.5,
            "height_max": 1.5,
            "spread_min": 0.8,
            "spread_max": 1.2,
            "soil_ph_min": 6.0,
            "soil_ph_max": 8.0,
            "water_needs": "low",
            "sun_exposure": "full_sun",
            "maintenance_level": "low",
            "bloom_period": "spring",
            "foliage_color": "green,silver",
            "is_native": True,
            "price_range": "low"
        },
        {
            "name": "Basilic",
            "scientific_name": "Ocimum basilicum",
            "category": "aromatiques",
            "climate_zones": ["Méditerranéen", "Atlantique", "Continental", "Tropical"],
            "hardiness_zone": 9,
            "height_min": 0.2,
            "height_max": 0.6,
            "spread_min": 0.3,
            "spread_max": 0.5,
            "soil_ph_min": 6.0,
            "soil_ph_max": 7.0,
            "water_needs": "medium",
            "sun_exposure": "full_sun",
            "maintenance_level": "medium",
            "bloom_period": "summer",
            "foliage_color": "green",
            "is_native": False,
            "price_range": "low"
        },
        
        # GRIMPANTES
        {
            "name": "Clématite",
            "scientific_name": "Clematis montana",
            "category": "grimpantes",
            "climate_zones": ["Atlantique", "Continental"],
            "hardiness_zone": 6,
            "height_min": 3.0,
            "height_max": 8.0,
            "spread_min": 2.0,
            "spread_max": 4.0,
            "soil_ph_min": 6.0,
            "soil_ph_max": 7.5,
            "water_needs": "medium",
            "sun_exposure": "partial_sun",
            "maintenance_level": "medium",
            "bloom_period": "late_spring",
            "foliage_color": "green",
            "is_native": False,
            "price_range": "medium"
        }
    ]
    
    created_count = 0
    for plant_data in plants_data:
        category = categories[plant_data["category"]]
        plant_data["category"] = category
        
        # Conversion des zones climatiques en JSON
        plant_data["climate_zones"] = plant_data["climate_zones"]
        
        plant, created = Plant.objects.get_or_create(
            scientific_name=plant_data["scientific_name"],
            defaults=plant_data
        )
        
        if created:
            created_count += 1
            print(f"✅ Créé: {plant.name} ({plant.scientific_name})")
        else:
            print(f"🔄 Existe: {plant.name}")
    
    return created_count

def main():
    print("🌱 Populate Base de Données Plantes TerraSketch")
    print("="*50)
    
    # Créer les catégories
    print("\n📂 Création catégories...")
    categories = create_plant_categories()
    
    # Créer les plantes
    print(f"\n🌿 Création plantes...")
    plant_count = create_essential_plants(categories)
    
    # Statistiques finales
    total_categories = PlantCategory.objects.count()
    total_plants = Plant.objects.count()
    
    print(f"\n📊 Résumé:")
    print(f"✅ Catégories: {total_categories}")
    print(f"✅ Plantes: {total_plants} ({plant_count} nouvelles)")
    
    # Répartition par zone climatique
    print(f"\n🌍 Répartition par zone:")
    zones = ["Atlantique", "Continental", "Méditerranéen", "Montagnard", "Tropical"]
    for zone in zones:
        count = Plant.objects.filter(climate_zones__contains=[zone]).count()
        print(f"  {zone}: {count} espèces")
    
    print(f"\n🎉 Base de données plantes prête pour le MVP!")
    print(f"▶️  Compatible avec le système IA de TerraSketch")

if __name__ == "__main__":
    main()