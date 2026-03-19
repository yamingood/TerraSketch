#!/usr/bin/env python
"""
Script d'importation de la base de données de plantes étendue
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.migration_minimal')
django.setup()

from apps.accounts.models import User
from apps.plants.models import Plant, PlantFamily, PlantStyle
from decimal import Decimal
import uuid

def load_plants_database(file_path):
    """Charge la base de données de plantes depuis le fichier JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def create_or_get_family(family_name):
    """Crée ou récupère une famille de plante"""
    family, created = PlantFamily.objects.get_or_create(
        name_latin=family_name,
        defaults={'name_fr': family_name}
    )
    if created:
        print(f"  ➕ Famille créée: {family_name}")
    return family

def map_field_values(plant_data):
    """Mappe les valeurs des champs vers le modèle Django"""
    mapping = {
        # Mappage des exigences solaires
        'sun_requirements': {
            'full_sun': 'full_sun',
            'partial_shade': 'partial_shade', 
            'shade': 'full_shade'
        },
        # Mappage des besoins en eau
        'watering_needs': {
            'low': 'low',
            'moderate': 'moderate',
            'high': 'high'
        },
        # Mappage des catégories vers types
        'category_to_type': {
            'arbuste_persistant': 'shrub',
            'arbuste_caduc': 'shrub',
            'arbre_ornemental': 'tree',
            'arbre_fruitier': 'tree',
            'vivace': 'perennial',
            'graminee': 'grass',
            'grimpante': 'climber',
            'conifere': 'tree',
            'rosier': 'shrub',
            'plante_mediterraneenne': 'perennial',
            'fruitier_arbustif': 'shrub',
            'plante_bord_eau': 'aquatic',
            'bulbe': 'bulb',
            'couvre_sol': 'groundcover',
            'fougere': 'perennial',
            'aromatique': 'perennial'
        }
    }
    
    mapped_data = {}
    
    # Nom commun français et latin
    mapped_data['name_common_fr'] = plant_data.get('name_common', '')
    mapped_data['name_latin'] = plant_data.get('name_latin', '')
    
    # Type de plante basé sur la catégorie
    category = plant_data.get('category', 'perennial')
    mapped_data['type'] = mapping['category_to_type'].get(category, 'perennial')
    
    # Dimensions en centimètres
    if plant_data.get('size_adult_height'):
        mapped_data['height_adult_max_cm'] = int(plant_data['size_adult_height'] * 100)
    if plant_data.get('size_adult_width'):
        mapped_data['width_adult_max_cm'] = int(plant_data['size_adult_width'] * 100)
    
    # Exposition solaire
    sun_req = plant_data.get('sun_requirements')
    if sun_req in mapping['sun_requirements']:
        mapped_data['sun_exposure'] = mapping['sun_requirements'][sun_req]
    
    # Besoins en eau
    water_need = plant_data.get('watering_needs')
    if water_need in mapping['watering_needs']:
        mapped_data['water_need'] = mapping['watering_needs'][water_need]
    
    # Feuillage (par défaut basé sur la catégorie)
    if 'persistant' in category:
        mapped_data['foliage'] = 'evergreen'
    elif 'caduc' in category:
        mapped_data['foliage'] = 'deciduous'
    else:
        mapped_data['foliage'] = 'deciduous'  # Par défaut
    
    # Mois de floraison
    bloom_season = plant_data.get('bloom_season')
    if bloom_season:
        season_to_months = {
            'printemps': [3, 4, 5],
            'été': [6, 7, 8],
            'automne': [9, 10, 11],
            'hiver': [12, 1, 2]
        }
        mapped_data['flowering_months'] = season_to_months.get(bloom_season, [])
    else:
        mapped_data['flowering_months'] = []
    
    # Résistance au froid (mapping approximatif des zones)
    hardiness = plant_data.get('hardiness_zone', '')
    zone_to_temp = {
        'Z5': -25, 'Z6': -20, 'Z7': -15, 'Z8': -10, 'Z9': -5
    }
    mapped_data['frost_resistance_min_c'] = zone_to_temp.get(hardiness, -10)
    
    # Racines invasives
    root_type = plant_data.get('root_type')
    mapped_data['is_invasive'] = (root_type == 'invasive')
    
    # Zones climatiques
    climate_zones = plant_data.get('climate_zones', [])
    mapped_data['climate_zones'] = climate_zones
    
    # Préférences de sol (dictionnaire simple)
    mapped_data['soil_preference'] = {
        'drainage': 'well_drained',
        'ph': 'neutral',
        'type': 'any'
    }
    
    # Autres champs avec valeurs par défaut
    mapped_data['growth_rate'] = 'moderate'
    mapped_data['flowering_color'] = ''
    mapped_data['is_drought_resistant'] = (water_need == 'low')
    mapped_data['attracts_pollinators'] = True  # Par défaut
    
    return mapped_data

def import_plants():
    """Importe toutes les plantes depuis le fichier JSON"""
    file_path = '/Users/yamingoudou/Documents/TERRASKETCH/terrasketch_plants_database.json'
    
    print("🌿 Importation de la base de données de plantes étendue...")
    
    # Charger les données
    data = load_plants_database(file_path)
    plants_data = data.get('plants', [])
    
    print(f"📊 {len(plants_data)} plantes à importer")
    
    # Statistiques
    imported_count = 0
    existing_count = 0
    error_count = 0
    
    for plant_data in plants_data:
        try:
            # Créer ou récupérer la famille
            family_name = plant_data.get('family', 'Unknown')
            family = create_or_get_family(family_name)
            
            # Mapper les données
            mapped_data = map_field_values(plant_data)
            mapped_data['family'] = family
            
            # Créer la plante
            name_latin = mapped_data['name_latin']
            plant, created = Plant.objects.get_or_create(
                name_latin=name_latin,
                defaults=mapped_data
            )
            
            if created:
                print(f"  ➕ {plant.name_common_fr} ({plant.name_latin})")
                imported_count += 1
                
                # Créer les affinités de style si spécifiées
                styles_list = plant_data.get('styles', [])
                for style_name in styles_list:
                    # Convertir le style en choix valide pour le modèle
                    style_mapping = {
                        'Méditerranéen': 'mediterranean',
                        'Contemporain': 'contemporary', 
                        'Anglais': 'countryside',
                        'Japonais': 'japanese',
                        'Naturel': 'countryside',
                        'Classique': 'contemporary',
                        'Tropical': 'tropical'
                    }
                    
                    style_choice = style_mapping.get(style_name, 'contemporary')
                    PlantStyle.objects.get_or_create(
                        plant=plant,
                        style=style_choice,
                        defaults={'affinity_score': 8}  # Score par défaut
                    )
            else:
                existing_count += 1
                
        except Exception as e:
            print(f"  ❌ Erreur avec {plant_data.get('name_latin', 'Inconnu')}: {e}")
            error_count += 1
    
    print(f"\n🎉 Importation terminée!")
    print(f"  ➕ {imported_count} nouvelles plantes importées")
    print(f"  ⏭️  {existing_count} plantes déjà existantes")
    print(f"  ❌ {error_count} erreurs")
    print(f"\n📊 Total en base: {Plant.objects.count()} plantes")
    print(f"📊 Familles: {PlantFamily.objects.count()}")

if __name__ == '__main__':
    import_plants()