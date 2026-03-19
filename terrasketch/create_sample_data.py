#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.migration_minimal')
django.setup()

from apps.accounts.models import User
from apps.plants.models import Plant, PlantFamily, PlantStyle
from apps.projects.models import Project
from decimal import Decimal
import uuid

print("Création de données de test pour TerraSketch...")

# Récupérer l'utilisateur testeur
try:
    user = User.objects.get(email='testeur@terrasketch.com')
    print(f"✅ Utilisateur trouvé: {user.email}")
except User.DoesNotExist:
    print("❌ Utilisateur testeur non trouvé. Exécutez d'abord create_test_user.py")
    exit(1)

# Créer des familles de plantes
families_data = [
    {'name_fr': 'Rosacées', 'name_latin': 'Rosaceae'},
    {'name_fr': 'Lamiacées', 'name_latin': 'Lamiaceae'},
    {'name_fr': 'Astéracées', 'name_latin': 'Asteraceae'},
    {'name_fr': 'Oléacées', 'name_latin': 'Oleaceae'},
    {'name_fr': 'Cupressacées', 'name_latin': 'Cupressaceae'},
    {'name_fr': 'Sapindacées', 'name_latin': 'Sapindaceae'},
    {'name_fr': 'Buxacées', 'name_latin': 'Buxaceae'},
]

print("\n🌿 Création des familles de plantes...")
for family_data in families_data:
    family, created = PlantFamily.objects.get_or_create(
        name_latin=family_data['name_latin'],
        defaults={'name_fr': family_data['name_fr']}
    )
    if created:
        print(f"  ➕ {family.name_fr} ({family.name_latin})")

print("\n🎨 Les styles de plantes sont gérés via des relations...")

# Créer des plantes d'exemple
plants_data = [
    {
        'name_common_fr': 'Lavande vraie',
        'name_latin': 'Lavandula angustifolia',
        'family': 'Lamiaceae',
        'type': 'shrub',
        'height_adult_min_cm': 50,
        'height_adult_max_cm': 70,
        'width_adult_min_cm': 60,
        'width_adult_max_cm': 100,
        'growth_rate': 'moderate',
        'foliage': 'evergreen',
        'flowering_months': [6, 7, 8, 9],
        'flowering_color': 'purple',
        'is_drought_resistant': True,
        'frost_resistance_min_c': -15,
        'water_need': 'low',
        'sun_exposure': 'full_sun',
        'soil_preference': {'drainage': 'well_drained', 'type': 'any'},
        'is_invasive': False,
        'attracts_pollinators': True,
        'climate_zones': [5, 6, 7, 8, 9],
    },
    {
        'name_common_fr': 'Rose de jardin',
        'name_latin': 'Rosa gallica',
        'family': 'Rosaceae',
        'type': 'shrub',
        'height_adult_min_cm': 100,
        'height_adult_max_cm': 140,
        'width_adult_min_cm': 80,
        'width_adult_max_cm': 120,
        'growth_rate': 'moderate',
        'foliage': 'deciduous',
        'flowering_months': [5, 6, 7, 8, 9, 10],
        'flowering_color': 'pink',
        'is_drought_resistant': False,
        'frost_resistance_min_c': -20,
        'water_need': 'moderate',
        'sun_exposure': 'full_sun',
        'soil_preference': {'drainage': 'moist', 'type': 'rich', 'ph': 'neutral'},
        'is_invasive': False,
        'attracts_pollinators': True,
        'climate_zones': [4, 5, 6, 7, 8],
    },
    {
        'name_common_fr': 'Cyprès de Provence',
        'name_latin': 'Cupressus sempervirens',
        'family': 'Cupressaceae',
        'type': 'tree',
        'height_adult_min_cm': 1200,
        'height_adult_max_cm': 1800,
        'width_adult_min_cm': 150,
        'width_adult_max_cm': 250,
        'growth_rate': 'slow',
        'foliage': 'evergreen',
        'flowering_months': [],
        'flowering_color': '',
        'is_drought_resistant': True,
        'frost_resistance_min_c': -12,
        'water_need': 'low',
        'sun_exposure': 'full_sun',
        'soil_preference': {'drainage': 'well_drained', 'type': 'any'},
        'is_invasive': False,
        'attracts_pollinators': False,
        'climate_zones': [7, 8, 9, 10],
    },
    {
        'name_common_fr': 'Érable du Japon',
        'name_latin': 'Acer palmatum',
        'family': 'Sapindaceae',
        'type': 'tree',
        'height_adult_min_cm': 300,
        'height_adult_max_cm': 500,
        'width_adult_min_cm': 250,
        'width_adult_max_cm': 350,
        'growth_rate': 'slow',
        'foliage': 'deciduous',
        'flowering_months': [4, 5],
        'flowering_color': 'red',
        'is_drought_resistant': False,
        'frost_resistance_min_c': -18,
        'water_need': 'moderate',
        'sun_exposure': 'partial_shade',
        'soil_preference': {'drainage': 'well_drained', 'type': 'acidic', 'ph': 'acidic'},
        'is_invasive': False,
        'attracts_pollinators': False,
        'climate_zones': [5, 6, 7, 8],
    },
    {
        'name_common_fr': 'Buis commun',
        'name_latin': 'Buxus sempervirens',
        'family': 'Buxaceae',
        'type': 'shrub',
        'height_adult_min_cm': 100,
        'height_adult_max_cm': 200,
        'width_adult_min_cm': 100,
        'width_adult_max_cm': 200,
        'growth_rate': 'slow',
        'foliage': 'evergreen',
        'flowering_months': [3, 4],
        'flowering_color': 'yellow',
        'is_drought_resistant': False,
        'frost_resistance_min_c': -15,
        'water_need': 'moderate',
        'sun_exposure': 'partial_shade',
        'soil_preference': {'drainage': 'well_drained', 'type': 'any'},
        'is_invasive': False,
        'attracts_pollinators': False,
        'climate_zones': [6, 7, 8, 9],
    },
]

print("\n🌱 Création des plantes...")
for plant_data in plants_data:
    # Récupérer la famille
    family = PlantFamily.objects.get(name_latin=plant_data['family'])
    
    # Créer la plante
    plant_defaults = dict(plant_data)
    family_name = plant_defaults.pop('family')  # Remove the string reference
    plant_defaults['family'] = family
    
    plant, created = Plant.objects.get_or_create(
        name_latin=plant_data['name_latin'],
        defaults=plant_defaults
    )
    
    if created:
        print(f"  ➕ {plant.name_common_fr} ({plant.name_latin})")

# Créer des projets d'exemple
projects_data = [
    {
        'name': 'Jardin contemporain - Villa Marseille',
        'status': 'in_progress',
        'budget_total': Decimal('15000.00'),
        'budget_tier': 'premium',
        'phase_plan': True,
        'address': '123 Avenue de la République',
        'city': 'Marseille',
        'postal_code': '13001',
    },
    {
        'name': 'Terrasse végétalisée - Appartement Lyon',
        'status': 'completed',
        'budget_total': Decimal('5000.00'),
        'budget_tier': 'structured',
        'phase_plan': False,
        'address': '45 Rue de la Part-Dieu',
        'city': 'Lyon',
        'postal_code': '69003',
    },
    {
        'name': 'Jardin méditerranéen - Maison Toulouse',
        'status': 'draft',
        'budget_total': Decimal('8000.00'),
        'budget_tier': 'structured',
        'phase_plan': True,
        'address': '12 Place du Capitole',
        'city': 'Toulouse',
        'postal_code': '31000',
    },
]

print("\n🏡 Création des projets...")
for project_data in projects_data:
    project, created = Project.objects.get_or_create(
        name=project_data['name'],
        defaults={
            'user': user,
            'status': project_data['status'],
            'budget_total': project_data['budget_total'],
            'budget_tier': project_data['budget_tier'],
            'phase_plan': project_data['phase_plan'],
            'address': project_data['address'],
            'city': project_data['city'],
            'postal_code': project_data['postal_code'],
        }
    )
    if created:
        print(f"  ➕ {project.name}")

print("\n🎉 Données de test créées avec succès!")
print("\n📊 Résumé:")
print(f"  • {PlantFamily.objects.count()} familles de plantes")
print(f"  • {Plant.objects.count()} plantes")
print(f"  • {Project.objects.count()} projets")
print("\n🚀 La base de données est maintenant peuplée pour les tests!")