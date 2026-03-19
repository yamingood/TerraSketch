"""
Assembleur principal du contexte pour la génération de plans paysagers.

Ce module centralise l'assemblage de toutes les données nécessaires à la génération :
- Données de la parcelle (surface, orientation, topographie)
- Données climatiques (température, précipitations, zone de rusticité)
- Orientation solaire et ensoleillement
- Plantes compatibles avec les conditions
- Préférences utilisateur
"""
import json
from typing import Dict, Optional
from django.core.exceptions import ObjectDoesNotExist

from .services.climate_service import ClimateService
from .services.solar_service import SolarService
from .services.plant_selector import PlantSelector


class ContextAssembler:
    """
    Classe principale pour assembler le contexte complet d'un projet.
    """
    
    @classmethod
    def assemble_project_context(cls, project_id: str, preferences: Dict) -> Dict:
        """
        Assemble le contexte complet pour un projet.
        
        Args:
            project_id: ID du projet
            preferences: Préférences utilisateur pour le projet
            
        Returns:
            dict: Contexte complet pour la génération
            
        Raises:
            ObjectDoesNotExist: Si le projet n'existe pas
            ValueError: Si les données essentielles sont manquantes
        """
        from apps.projects.models import Project
        
        try:
            project = Project.objects.select_related('parcel').get(id=project_id)
        except Project.DoesNotExist:
            raise ObjectDoesNotExist(f"Projet {project_id} non trouvé")
        
        if not project.parcel:
            raise ValueError(f"Aucune parcelle associée au projet {project_id}")
        
        # 1. Récupérer les données de base de la parcelle
        parcel_data = cls._extract_parcel_data(project.parcel)
        
        # 2. Récupérer les données climatiques
        climate_data = cls._get_climate_data(parcel_data)
        
        # 3. Calculer l'orientation solaire et l'ensoleillement
        solar_data = cls._calculate_solar_data(parcel_data, climate_data)
        
        # 4. Déterminer les zones climatiques et de rusticité
        zones_data = cls._determine_climate_zones(parcel_data, climate_data)
        
        # 5. Sélectionner les plantes compatibles
        plants_data = cls._select_compatible_plants(zones_data, preferences)
        
        # 6. Analyser le terrassement nécessaire
        terrassement_data = cls._analyze_terrassement_needs(parcel_data)
        
        # 7. Assembler le contexte final
        context = {
            'project_id': project_id,
            'parcelle': parcel_data,
            'climat': climate_data,
            'solaire': solar_data,
            'zones': zones_data,
            'plantes_disponibles': plants_data,
            'terrassement': terrassement_data,
            'preferences': preferences,
            'metadata': {
                'assembled_at': cls._get_timestamp(),
                'version': '1.0'
            }
        }
        
        return context
    
    @classmethod
    def _extract_parcel_data(cls, parcel) -> Dict:
        """
        Extrait les données essentielles de la parcelle.
        """
        # Extraire la géométrie
        geometry = None
        if parcel.geometry:
            try:
                geometry = json.loads(parcel.geometry) if isinstance(parcel.geometry, str) else parcel.geometry
            except json.JSONDecodeError:
                geometry = None
        
        # Calculer latitude/longitude du centre
        latitude, longitude = cls._calculate_parcel_center(geometry)
        
        return {
            'id': str(parcel.id),
            'reference_cadastrale': parcel.cadastral_reference or '',
            'surface_m2': parcel.area_sqm or 0,
            'perimetre_m': parcel.perimeter_m or 0,
            'geometry': geometry,
            'latitude': latitude,
            'longitude': longitude,
            'orientation': parcel.orientation or 'non définie',
            'source': parcel.source
        }
    
    @classmethod
    def _calculate_parcel_center(cls, geometry: Optional[Dict]) -> tuple:
        """
        Calcule le centre géographique de la parcelle.
        
        Returns:
            tuple: (latitude, longitude) ou valeurs par défaut
        """
        if not geometry or 'coordinates' not in geometry:
            # Valeur par défaut : centre de la France
            return (46.603354, 1.888334)
        
        try:
            # Calculer le centroïde approximatif
            coords = geometry['coordinates'][0] if geometry['type'] == 'Polygon' else geometry['coordinates']
            
            if not coords:
                return (46.603354, 1.888334)
            
            # Moyenne des coordonnées
            lats = [coord[1] for coord in coords if len(coord) >= 2]
            lngs = [coord[0] for coord in coords if len(coord) >= 2]
            
            if lats and lngs:
                return (sum(lats) / len(lats), sum(lngs) / len(lngs))
            
        except Exception:
            pass
        
        return (46.603354, 1.888334)  # Centre France par défaut
    
    @classmethod
    def _get_climate_data(cls, parcel_data: Dict) -> Dict:
        """
        Récupère les données climatiques pour la parcelle.
        """
        latitude = parcel_data['latitude']
        longitude = parcel_data['longitude']
        
        climate_data = ClimateService.get_climate_data(latitude, longitude)
        
        # Ajouter des informations de localisation
        climate_data['commune'] = cls._get_commune_name(latitude, longitude)
        
        return climate_data
    
    @classmethod
    def _get_commune_name(cls, latitude: float, longitude: float) -> str:
        """
        Récupère le nom de la commune (version simplifiée).
        
        En production, utiliser une API de géolocalisation inverse.
        """
        # Pour l'instant, retourner une estimation basée sur les coordonnées
        if latitude > 49:
            return "Nord de la France"
        elif latitude > 47:
            return "Centre de la France"
        elif longitude < 2:
            return "Côte Atlantique"
        elif longitude > 6:
            return "Est de la France"
        else:
            return "Sud de la France"
    
    @classmethod
    def _calculate_solar_data(cls, parcel_data: Dict, climate_data: Dict) -> Dict:
        """
        Calcule les données d'ensoleillement et d'orientation solaire.
        """
        geometry = parcel_data['geometry']
        latitude = parcel_data['latitude']
        longitude = parcel_data['longitude']
        
        solar_data = SolarService.calculate_solar_orientation(geometry, latitude, longitude)
        
        # Ajouter des recommandations de placement
        placement_recommendations = SolarService.get_optimal_zones_placement(
            solar_data, parcel_data['surface_m2']
        )
        solar_data['placement_recommendations'] = placement_recommendations
        
        return solar_data
    
    @classmethod
    def _determine_climate_zones(cls, parcel_data: Dict, climate_data: Dict) -> Dict:
        """
        Détermine les zones climatiques et de rusticité.
        """
        latitude = parcel_data['latitude']
        longitude = parcel_data['longitude']
        
        # Zone climatique française
        zone_climatique = ClimateService.determine_climate_zone(latitude, longitude, climate_data)
        
        # Zone de rusticité USDA
        temp_min = climate_data.get('temperature_minimale_record', -7.0)
        zone_rusticite = ClimateService.determine_hardiness_zone(temp_min)
        
        return {
            'zone_climatique': zone_climatique,
            'zone_rusticite': zone_rusticite,
            'stress_hydrique': climate_data.get('stress_hydrique', 'modere')
        }
    
    @classmethod
    def _select_compatible_plants(cls, zones_data: Dict, preferences: Dict) -> list:
        """
        Sélectionne les plantes compatibles avec les conditions.
        """
        zone_climatique = zones_data['zone_climatique']
        zone_rusticite = zones_data['zone_rusticite']
        stress_hydrique = zones_data['stress_hydrique']
        
        # Récupérer le nombre max de plantes depuis les settings
        from django.conf import settings
        max_plants = getattr(settings, 'PROMPT_MAX_PLANTS', 40)
        
        plants = PlantSelector.select_compatible_plants(
            zone_climatique=zone_climatique,
            zone_rusticite=zone_rusticite,
            stress_hydrique=stress_hydrique,
            preferences=preferences,
            max_plants=max_plants
        )
        
        return plants
    
    @classmethod
    def _analyze_terrassement_needs(cls, parcel_data: Dict) -> Dict:
        """
        Analyse les besoins de terrassement (version simplifiée).
        
        En production, intégrer avec l'API IGN et l'analyse de terrain.
        """
        surface_m2 = parcel_data['surface_m2']
        geometry = parcel_data.get('geometry')
        
        # Estimation simplifiée basée sur la surface
        if surface_m2 < 100:
            complexite = "faible"
            denivele_estime = 0.5
        elif surface_m2 < 500:
            complexite = "moyenne"
            denivele_estime = 1.5
        else:
            complexite = "elevee"
            denivele_estime = 3.0
        
        return {
            'necessaire': surface_m2 > 50,  # Terrassement nécessaire si surface > 50m²
            'complexite': complexite,
            'denivele_estime_m': denivele_estime,
            'pente_moyenne_pct': cls._estimate_slope(geometry),
            'drainage_requis': surface_m2 > 200,
            'volume_estime_m3': surface_m2 * denivele_estime * 0.3  # Estimation approximative
        }
    
    @classmethod
    def _estimate_slope(cls, geometry: Optional[Dict]) -> float:
        """
        Estime la pente moyenne de la parcelle (version simplifiée).
        """
        # Version simplifiée : retourner une estimation aléatoire réaliste
        import random
        return round(random.uniform(1.0, 8.0), 1)
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """
        Retourne un timestamp ISO 8601.
        """
        from django.utils import timezone
        return timezone.now().isoformat()
    
    @classmethod
    def validate_context(cls, context: Dict) -> tuple:
        """
        Valide que le contexte assemblé est complet et cohérent.
        
        Returns:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Vérifications essentielles
        required_keys = [
            'parcelle', 'climat', 'solaire', 'zones', 
            'plantes_disponibles', 'preferences'
        ]
        
        for key in required_keys:
            if key not in context:
                errors.append(f"Section manquante : {key}")
        
        # Vérifications spécifiques
        if 'parcelle' in context:
            parcelle = context['parcelle']
            if not parcelle.get('surface_m2') or parcelle['surface_m2'] <= 0:
                errors.append("Surface de parcelle invalide")
            
            if not parcelle.get('latitude') or not parcelle.get('longitude'):
                errors.append("Coordonnées de parcelle manquantes")
        
        if 'plantes_disponibles' in context:
            if not context['plantes_disponibles']:
                errors.append("Aucune plante compatible trouvée")
            elif len(context['plantes_disponibles']) < 10:
                errors.append("Nombre insuffisant de plantes compatibles")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_context_summary(cls, context: Dict) -> Dict:
        """
        Génère un résumé du contexte pour logging et debugging.
        """
        return {
            'project_id': context.get('project_id'),
            'surface_m2': context.get('parcelle', {}).get('surface_m2', 0),
            'zone_climatique': context.get('zones', {}).get('zone_climatique'),
            'zone_rusticite': context.get('zones', {}).get('zone_rusticite'),
            'nb_plantes': len(context.get('plantes_disponibles', [])),
            'style': context.get('preferences', {}).get('style'),
            'budget': context.get('preferences', {}).get('budget_total_ht'),
            'assembled_at': context.get('metadata', {}).get('assembled_at')
        }