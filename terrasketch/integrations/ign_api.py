"""
Services d'intégration avec l'API IGN/Géoplateforme
pour l'enrichissement des données cadastrales
"""

import requests
import xml.etree.ElementTree as ET
import json
import logging
from django.conf import settings
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TopographieData:
    """Données topographiques d'une parcelle"""
    altitude_min: float
    altitude_max: float
    denivele_m: float
    pente_moyenne_pct: float
    terrassement_complexite: str  # faible, modere, eleve

@dataclass
class GeocodeResult:
    """Résultat de géocodage IGN"""
    latitude: float
    longitude: float
    address: str
    city: str
    postal_code: str
    accuracy: float

class IGNAPIService:
    """Service principal pour les appels API IGN"""
    
    def __init__(self):
        self.api_key = settings.IGN_API_KEY
        self.services = settings.IGN_SERVICES
        self.session = requests.Session()
        
    def _make_request(self, url: str, params: dict = None, timeout: int = 30) -> requests.Response:
        """Effectue une requête HTTP avec gestion d'erreurs"""
        try:
            params = params or {}
            
            # Ajouter la clé API seulement pour les services data.geopf.fr
            if 'data.geopf.fr' in url:
                params['key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur requête IGN API: {e}")
            raise
    
    def geocode_address(self, address: str) -> Optional[GeocodeResult]:
        """
        Géocode une adresse avec l'API IGN (nouvelle API data.geopf.fr)
        
        Args:
            address: Adresse à géocoder
            
        Returns:
            GeocodeResult ou None si non trouvé
        """
        try:
            url = self.services['geocodage']
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            
            response = self._make_request(url, params)
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                coordinates = feature['geometry']['coordinates']
                properties = feature['properties']
                
                return GeocodeResult(
                    latitude=coordinates[1],
                    longitude=coordinates[0],
                    address=properties.get('label', address),
                    city=properties.get('city', ''),
                    postal_code=properties.get('postcode', ''),
                    accuracy=properties.get('score', 0.8)  # Score de confiance
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur géocodage IGN: {e}")
            return None
    
    def get_elevation_data(self, longitude: float, latitude: float, 
                          buffer_meters: int = 50) -> Optional[TopographieData]:
        """
        Récupère les données d'élévation pour un point avec l'API Altimétrie IGN
        
        Args:
            longitude: Longitude du point central
            latitude: Latitude du point central  
            buffer_meters: Rayon autour du point pour calculer pente/dénivelé
            
        Returns:
            TopographieData ou None si erreur
        """
        try:
            # ID de ressource pour l'altimétrie IGN (à ajuster selon la ressource disponible)
            resource_id = 'ign_rge_alti_wld'  # Ressource altimétrique mondiale IGN
            url = f"{self.services['altimetrie']}/{resource_id}"
            
            # Requête pour l'altitude du point central
            params = {
                'lon': longitude,
                'lat': latitude,
            }
            
            response = self._make_request(url, params)
            data = response.json()
            
            # La structure exacte dépend de l'API IGN - adaptation nécessaire selon doc
            altitude_center = None
            if isinstance(data, dict):
                if 'elevation' in data:
                    altitude_center = data['elevation']
                elif 'z' in data:
                    altitude_center = data['z']
                elif 'alt' in data:
                    altitude_center = data['alt']
            elif isinstance(data, (int, float)):
                altitude_center = data
            
            if altitude_center is None:
                return None
            
            # Calculer quelques points autour pour estimer la pente
            buffer_deg = buffer_meters / 111111  # Approximation: 1 degré ≈ 111km
            
            points_around = [
                (longitude + buffer_deg, latitude),
                (longitude - buffer_deg, latitude),
                (longitude, latitude + buffer_deg),
                (longitude, latitude - buffer_deg)
            ]
            
            elevations = [altitude_center]
            
            for lon, lat in points_around:
                try:
                    params_point = {
                        'lon': lon,
                        'lat': lat,
                    }
                    response_point = self._make_request(url, params_point)
                    data_point = response_point.json()
                    
                    elev = None
                    if isinstance(data_point, dict):
                        if 'elevation' in data_point:
                            elev = data_point['elevation']
                        elif 'z' in data_point:
                            elev = data_point['z']
                        elif 'alt' in data_point:
                            elev = data_point['alt']
                    elif isinstance(data_point, (int, float)):
                        elev = data_point
                        
                    if elev is not None:
                        elevations.append(elev)
                except:
                    continue
            
            # Calculer les statistiques
            altitude_min = min(elevations)
            altitude_max = max(elevations)
            denivele = altitude_max - altitude_min
            
            # Estimer la pente moyenne (simplifiée)
            if denivele > 0:
                distance_avg = buffer_meters * 2  # Distance moyenne entre points
                pente_pct = (denivele / distance_avg) * 100
            else:
                pente_pct = 0.0
            
            # Déterminer la complexité de terrassement
            if pente_pct < 5 and denivele < 2:
                complexite = 'faible'
            elif pente_pct < 15 and denivele < 5:
                complexite = 'modere'
            else:
                complexite = 'eleve'
            
            return TopographieData(
                altitude_min=altitude_min,
                altitude_max=altitude_max,
                denivele_m=denivele,
                pente_moyenne_pct=round(pente_pct, 1),
                terrassement_complexite=complexite
            )
            
        except Exception as e:
            logger.error(f"Erreur données élévation IGN: {e}")
            return None
    
    def get_cadastral_info(self, longitude: float, latitude: float) -> Optional[Dict]:
        """
        Récupère les informations cadastrales officielles IGN pour un point
        Utilise l'API Apicarto WFS-Géoportail
        
        Args:
            longitude: Longitude du point
            latitude: Latitude du point
            
        Returns:
            Dict avec les informations cadastrales ou None si erreur
        """
        try:
            url = self.services['cadastre']
            
            # Construire la géométrie point en GeoJSON
            point_geojson = json.dumps({
                "type": "Point",
                "coordinates": [longitude, latitude]
            })
            
            # Essayer plusieurs sources cadastrales disponibles
            cadastre_sources = [
                'BDPARCELLAIRE_V2:parcelle',
                'CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle', 
                'BDTOPO_V3:batiment',
                'BDTOPO_V3:commune'
            ]
            
            for source in cadastre_sources:
                try:
                    params = {
                        'source': source,
                        'geom': point_geojson,
                        'format': 'json',
                        'limit': 1
                    }
                    
                    response = self.session.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('features') and len(data['features']) > 0:
                        feature = data['features'][0]
                        properties = feature.get('properties', {})
                        
                        # Extraire les informations selon le type de source
                        cadastre_info = {
                            'source_type': source,
                            'id_parcelle': properties.get('id') or properties.get('idu') or properties.get('numero'),
                            'section': properties.get('section'),
                            'numero': properties.get('numero') or properties.get('numpar'),
                            'commune': properties.get('commune') or properties.get('nomcom') or properties.get('nom'),
                            'code_insee': properties.get('insee') or properties.get('codinse'),
                            'surface_officielle': properties.get('contenance') or properties.get('supf'),
                            'prefixe': properties.get('prefixe'),
                            'code_arr': properties.get('codarr'),
                            'geometry': feature.get('geometry'),
                            'all_properties': properties  # Garder toutes les propriétés pour debug
                        }
                        
                        # Nettoyer les valeurs None
                        cadastre_info = {k: v for k, v in cadastre_info.items() if v is not None}
                        
                        logger.info(f"Informations cadastrales trouvées pour {longitude},{latitude} "
                                   f"(source: {source}): parcelle={cadastre_info.get('id_parcelle')}")
                        
                        return cadastre_info
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Source {source} non disponible: {e}")
                    continue
                    
            logger.info(f"Aucune donnée cadastrale trouvée pour le point {longitude},{latitude} "
                       f"dans les sources: {', '.join(cadastre_sources)}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération données cadastrales: {e}")
            return None


def enrich_parcelle_with_ign(longitude: float, latitude: float, 
                           address: str = None) -> Dict:
    """
    Fonction utilitaire pour enrichir les données d'une parcelle avec l'API IGN
    
    Args:
        longitude: Longitude du centre de la parcelle
        latitude: Latitude du centre de la parcelle
        address: Adresse pour validation (optionnel)
        
    Returns:
        Dictionnaire avec toutes les données enrichies IGN
    """
    ign_service = IGNAPIService()
    result = {
        'ign_enriched': True,
        'topographie': None,
        'geocode': None,
        'cadastre_officiel': None,
        'erreurs': []
    }
    
    try:
        # 1. Données topographiques
        topo_data = ign_service.get_elevation_data(longitude, latitude)
        if topo_data:
            result['topographie'] = {
                'altitude_min': topo_data.altitude_min,
                'altitude_max': topo_data.altitude_max,
                'denivele_m': topo_data.denivele_m,
                'pente_moyenne_pct': topo_data.pente_moyenne_pct,
                'terrassement_complexite': topo_data.terrassement_complexite
            }
        else:
            result['erreurs'].append('Impossible de récupérer les données topographiques')
    
        # 2. Géocodage de l'adresse si fournie
        if address:
            geocode_result = ign_service.geocode_address(address)
            if geocode_result:
                result['geocode'] = {
                    'latitude': geocode_result.latitude,
                    'longitude': geocode_result.longitude,
                    'address': geocode_result.address,
                    'city': geocode_result.city,
                    'postal_code': geocode_result.postal_code,
                    'accuracy': geocode_result.accuracy
                }
            else:
                result['erreurs'].append('Géocodage de l\'adresse impossible')
        
        # 3. Informations cadastrales officielles
        cadastre_data = ign_service.get_cadastral_info(longitude, latitude)
        if cadastre_data:
            result['cadastre_officiel'] = cadastre_data
        else:
            result['erreurs'].append('Données cadastrales officielles non disponibles')
            
    except Exception as e:
        logger.error(f"Erreur enrichissement IGN global: {e}")
        result['erreurs'].append(f'Erreur technique: {str(e)}')
        result['ign_enriched'] = False
    
    return result