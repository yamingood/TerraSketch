"""
Service d'intégration IGN pour l'enrichissement géographique des parcelles
"""
import asyncio
import httpx
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from shapely.geometry import Polygon, Point
from shapely import wkt

from ..models import IGNUsageLog

logger = logging.getLogger(__name__)


class IGNServiceError(Exception):
    """Erreur générale du service IGN"""
    pass


class IGNQuotaExceededError(IGNServiceError):
    """Quota IGN dépassé"""
    pass


class IGNRateLimitError(IGNServiceError):
    """Rate limit IGN dépassé"""
    pass


class IGNService:
    """Service d'intégration IGN pour enrichissement géographique"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'IGN_API_KEY', None)
        if not self.api_key:
            logger.warning("IGN_API_KEY not configured - IGN enrichment disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.base_urls = {
            'geocoding': f'https://wxs.ign.fr/{self.api_key}/geoportail/geocodage/rest',
            'elevation': f'https://wxs.ign.fr/{self.api_key}/alti/rest',
            'wfs': f'https://wxs.ign.fr/{self.api_key}/wfs',
            'wmts': f'https://wxs.ign.fr/{self.api_key}/wmts'
        }
        
        # Configuration rate limiting
        self.requests_per_second = getattr(settings, 'IGN_REQUESTS_PER_SECOND', 10)
        self.daily_quota = getattr(settings, 'IGN_DAILY_QUOTA', 100000)
        
        # Client HTTP asynchrone
        self.timeout = httpx.Timeout(30.0, connect=5.0)
    
    async def _make_request(self, method: str, url: str, params: Optional[Dict] = None, 
                           json_data: Optional[Dict] = None, endpoint: str = '') -> Dict:
        """Effectue une requête HTTP vers IGN avec gestion erreurs et monitoring"""
        
        if not self.enabled:
            raise IGNServiceError("IGN service is disabled (no API key)")
        
        # Vérification quota
        self._check_quota()
        
        # Rate limiting
        await self._rate_limit()
        
        start_time = time.time()
        success = False
        response_status = 0
        error_message = None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers={
                        'User-Agent': 'TerraSketch/1.0 (contact@terrasketch.fr)',
                        'Accept': 'application/json'
                    }
                )
                
                response_status = response.status_code
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 429:
                    raise IGNRateLimitError("Rate limit IGN dépassé")
                
                if response.status_code >= 400:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                    raise IGNServiceError(error_message)
                
                result = response.json()
                success = True
                
                # Log utilisation
                self._log_usage(endpoint, response_status, response_time_ms, success)
                
                # Mise à jour quota
                self._update_quota_counter()
                
                return result
                
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            # Log échec
            self._log_usage(endpoint, response_status, response_time_ms, success, error_message)
            
            raise
    
    def _check_quota(self):
        """Vérifie le quota quotidien IGN"""
        today = timezone.now().date()
        daily_usage = cache.get(f'ign_usage_daily_{today}', 0)
        
        if daily_usage >= self.daily_quota:
            raise IGNQuotaExceededError(f"Quota IGN quotidien dépassé: {daily_usage}/{self.daily_quota}")
    
    async def _rate_limit(self):
        """Implémente le rate limiting"""
        last_request_time = cache.get('ign_last_request_time', 0)
        min_interval = 1.0 / self.requests_per_second
        
        elapsed = time.time() - last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        
        cache.set('ign_last_request_time', time.time(), timeout=60)
    
    def _update_quota_counter(self):
        """Met à jour le compteur de quota"""
        today = timezone.now().date()
        cache_key = f'ign_usage_daily_{today}'
        current = cache.get(cache_key, 0)
        cache.set(cache_key, current + 1, timeout=86400)  # 24h
    
    def _log_usage(self, endpoint: str, status: int, response_time: int, 
                   success: bool, error: Optional[str] = None):
        """Log utilisation API IGN"""
        try:
            IGNUsageLog.objects.create(
                endpoint=endpoint,
                response_status=status,
                response_time_ms=response_time,
                success=success,
                error_message=error
            )
        except Exception as e:
            logger.error(f"Erreur logging IGN: {e}")
    
    async def get_elevation_profile(self, coordinates: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Récupère le profil altimétrique pour une série de coordonnées
        
        Args:
            coordinates: Liste de tuples (longitude, latitude)
            
        Returns:
            Dict contenant le profil altimétrique
        """
        if not coordinates:
            raise ValueError("Coordinates list cannot be empty")
        
        # Limiter le nombre de points pour éviter les timeouts
        if len(coordinates) > 50:
            # Échantillonnage des coordonnées
            step = len(coordinates) // 50
            coordinates = coordinates[::step]
        
        # Préparer les coordonnées pour l'API IGN
        coords_str = '|'.join([f'{lon},{lat}' for lon, lat in coordinates])
        
        params = {
            'lon': coords_str.split('|')[0].split(',')[0],
            'lat': coords_str.split('|')[0].split(',')[1],
            'zonly': 'false',
            'output': 'json'
        }
        
        url = f"{self.base_urls['elevation']}/elevation.json"
        
        try:
            # Pour MVP, on fait plusieurs requêtes ponctuelles
            elevations = []
            for i, (lon, lat) in enumerate(coordinates[:10]):  # Limite à 10 points pour MVP
                point_params = {
                    'lon': lon,
                    'lat': lat,
                    'zonly': 'false',
                    'output': 'json'
                }
                
                result = await self._make_request('GET', url, params=point_params, endpoint='elevation')
                
                if 'elevations' in result and result['elevations']:
                    elevation = result['elevations'][0]['z']
                    elevations.append({
                        'distance': i * 10,  # Distance approximative
                        'longitude': lon,
                        'latitude': lat,
                        'elevation': elevation
                    })
            
            if not elevations:
                raise IGNServiceError("Aucune donnée d'altitude trouvée")
            
            # Calculer statistiques
            elevation_values = [point['elevation'] for point in elevations]
            min_elevation = min(elevation_values)
            max_elevation = max(elevation_values)
            avg_elevation = sum(elevation_values) / len(elevation_values)
            
            # Analyser les pentes
            slope_analysis = self._analyze_slopes(elevations)
            
            return {
                'min': round(min_elevation, 2),
                'max': round(max_elevation, 2),
                'average': round(avg_elevation, 2),
                'profile': elevations,
                'slope_analysis': slope_analysis
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération profil altimétrique: {e}")
            raise IGNServiceError(f"Erreur altitude IGN: {e}")
    
    def _analyze_slopes(self, elevations: List[Dict]) -> Dict[str, Any]:
        """Analyse les pentes à partir du profil altimétrique"""
        if len(elevations) < 2:
            return {'max_slope_pct': 0, 'average_slope_pct': 0, 'areas': []}
        
        slopes = []
        for i in range(1, len(elevations)):
            prev_point = elevations[i-1]
            curr_point = elevations[i]
            
            # Distance horizontale (approximation)
            distance = ((curr_point['longitude'] - prev_point['longitude']) ** 2 + 
                       (curr_point['latitude'] - prev_point['latitude']) ** 2) ** 0.5 * 111000  # Conversion degrés -> mètres
            
            if distance > 0:
                elevation_diff = curr_point['elevation'] - prev_point['elevation']
                slope_pct = abs(elevation_diff / distance) * 100
                slopes.append(slope_pct)
        
        if not slopes:
            return {'max_slope_pct': 0, 'average_slope_pct': 0, 'areas': []}
        
        max_slope = max(slopes)
        avg_slope = sum(slopes) / len(slopes)
        
        # Catégorisation des pentes
        gentle_slopes = len([s for s in slopes if s < 5])
        moderate_slopes = len([s for s in slopes if 5 <= s < 15])
        steep_slopes = len([s for s in slopes if s >= 15])
        
        total_segments = len(slopes)
        
        areas = [
            {'slope_range': '0-5%', 'area_pct': round((gentle_slopes / total_segments) * 100, 1)},
            {'slope_range': '5-15%', 'area_pct': round((moderate_slopes / total_segments) * 100, 1)},
            {'slope_range': '15%+', 'area_pct': round((steep_slopes / total_segments) * 100, 1)}
        ]
        
        return {
            'max_slope_pct': round(max_slope, 1),
            'average_slope_pct': round(avg_slope, 1),
            'areas': areas
        }
    
    async def reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """
        Géocodage inverse pour obtenir l'adresse à partir de coordonnées
        
        Args:
            longitude: Longitude
            latitude: Latitude
            
        Returns:
            Dict contenant les informations d'adresse
        """
        params = {
            'lon': longitude,
            'lat': latitude,
            'returntruegeometry': 'false',
            'output': 'json'
        }
        
        url = f"{self.base_urls['geocoding']}/reverse.json"
        
        try:
            result = await self._make_request('GET', url, params=params, endpoint='geocoding_reverse')
            
            if 'features' not in result or not result['features']:
                # Fallback avec données simulées basées sur coordonnées
                return self._generate_fallback_address(longitude, latitude)
            
            feature = result['features'][0]
            properties = feature.get('properties', {})
            
            # Extraction des informations
            address_components = []
            if properties.get('housenumber'):
                address_components.append(properties['housenumber'])
            if properties.get('street'):
                address_components.append(properties['street'])
            
            full_address = ' '.join(address_components)
            if properties.get('postcode') and properties.get('city'):
                full_address += f", {properties['postcode']} {properties['city']}"
            
            return {
                'normalized': full_address or f"Coordonnées {latitude:.4f}, {longitude:.4f}",
                'insee_code': properties.get('citycode', ''),
                'department': properties.get('postcode', '')[:2] if properties.get('postcode') else '',
                'region': self._get_region_from_department(properties.get('postcode', '')[:2] if properties.get('postcode') else ''),
                'city': properties.get('city', ''),
                'postcode': properties.get('postcode', ''),
                'quality_score': self._calculate_quality_score(properties)
            }
            
        except Exception as e:
            logger.error(f"Erreur géocodage inverse: {e}")
            return self._generate_fallback_address(longitude, latitude)
    
    def _generate_fallback_address(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """Génère une adresse de fallback basée sur les coordonnées"""
        # Détermination approximative de la région basée sur les coordonnées
        department = self._estimate_department_from_coords(longitude, latitude)
        region = self._get_region_from_department(department)
        
        return {
            'normalized': f"Parcelle {latitude:.4f}, {longitude:.4f}",
            'insee_code': '',
            'department': department,
            'region': region,
            'city': '',
            'postcode': '',
            'quality_score': 0.3  # Score bas pour fallback
        }
    
    def _estimate_department_from_coords(self, longitude: float, latitude: float) -> str:
        """Estimation approximative du département basée sur les coordonnées"""
        # Zones approximatives (simplifié pour MVP)
        if 2.0 <= longitude <= 2.6 and 48.8 <= latitude <= 49.0:
            return "75"  # Paris
        elif 1.3 <= longitude <= 2.9 and 48.1 <= latitude <= 49.2:
            return "78"  # Région parisienne
        elif 5.3 <= longitude <= 5.5 and 43.2 <= latitude <= 43.4:
            return "13"  # Marseille
        elif 1.4 <= longitude <= 1.5 and 43.5 <= latitude <= 43.7:
            return "31"  # Toulouse
        else:
            return "00"  # Inconnu
    
    def _get_region_from_department(self, department: str) -> str:
        """Mapping département -> région (simplifié)"""
        region_mapping = {
            '75': '11', '77': '11', '78': '11', '91': '11', '92': '11', '93': '11', '94': '11', '95': '11',  # Île-de-France
            '13': '93', '83': '93', '84': '93', '04': '93', '05': '93', '06': '93',  # PACA
            '31': '76', '09': '76', '12': '76', '32': '76', '46': '76', '65': '76', '81': '76', '82': '76',  # Occitanie
        }
        return region_mapping.get(department, '00')
    
    def _calculate_quality_score(self, properties: Dict) -> float:
        """Calcule un score de qualité pour le géocodage"""
        score = 0.0
        
        if properties.get('housenumber'):
            score += 0.4
        if properties.get('street'):
            score += 0.3
        if properties.get('city'):
            score += 0.2
        if properties.get('postcode'):
            score += 0.1
        
        return min(score, 1.0)
    
    async def get_land_cover(self, polygon_geojson: Dict) -> Dict[str, Any]:
        """
        Récupère les données d'occupation du sol OCS GE
        
        Args:
            polygon_geojson: Polygone au format GeoJSON
            
        Returns:
            Dict contenant les données d'occupation du sol
        """
        # Pour MVP, on simule les données OCS GE en analysant le contexte géographique
        try:
            coordinates = polygon_geojson['coordinates'][0]
            
            # Calcul du centroïde
            polygon = Polygon(coordinates)
            centroid = polygon.centroid
            
            # Simulation basée sur la localisation
            land_cover = self._simulate_land_cover(centroid.x, centroid.y, polygon.area)
            
            return land_cover
            
        except Exception as e:
            logger.error(f"Erreur récupération occupation du sol: {e}")
            # Fallback avec données par défaut
            return {
                'ocs_ge_version': '2022_simulated',
                'categories': [
                    {'code': '131', 'label': 'Espaces verts urbains', 'area_pct': 60.0},
                    {'code': '211', 'label': 'Zones résidentielles', 'area_pct': 40.0}
                ],
                'vegetation_cover_pct': 60.0,
                'artificial_cover_pct': 40.0,
                'water_cover_pct': 0.0,
                'agricultural_cover_pct': 0.0
            }
    
    def _simulate_land_cover(self, longitude: float, latitude: float, area_m2: float) -> Dict[str, Any]:
        """Simule les données d'occupation du sol basées sur la localisation"""
        
        # Classification approximative basée sur les coordonnées
        if self._is_urban_area(longitude, latitude):
            if area_m2 < 500:  # Petite parcelle urbaine
                categories = [
                    {'code': '211', 'label': 'Zones résidentielles', 'area_pct': 70.0},
                    {'code': '131', 'label': 'Espaces verts urbains', 'area_pct': 30.0}
                ]
                vegetation_pct = 30.0
                artificial_pct = 70.0
            else:  # Grande parcelle urbaine
                categories = [
                    {'code': '131', 'label': 'Espaces verts urbains', 'area_pct': 60.0},
                    {'code': '211', 'label': 'Zones résidentielles', 'area_pct': 40.0}
                ]
                vegetation_pct = 60.0
                artificial_pct = 40.0
        else:  # Zone périurbaine/rurale
            categories = [
                {'code': '131', 'label': 'Espaces verts urbains', 'area_pct': 80.0},
                {'code': '211', 'label': 'Zones résidentielles', 'area_pct': 20.0}
            ]
            vegetation_pct = 80.0
            artificial_pct = 20.0
        
        return {
            'ocs_ge_version': '2022_simulated',
            'categories': categories,
            'vegetation_cover_pct': vegetation_pct,
            'artificial_cover_pct': artificial_pct,
            'water_cover_pct': 0.0,
            'agricultural_cover_pct': 0.0
        }
    
    def _is_urban_area(self, longitude: float, latitude: float) -> bool:
        """Détermine si les coordonnées sont en zone urbaine"""
        # Zones urbaines approximatives (simplifié pour MVP)
        urban_zones = [
            (2.0, 2.6, 48.8, 49.0),    # Paris
            (5.3, 5.5, 43.2, 43.4),    # Marseille
            (1.4, 1.5, 43.5, 43.7),    # Toulouse
            (4.8, 4.9, 45.7, 45.8),    # Lyon
        ]
        
        for min_lon, max_lon, min_lat, max_lat in urban_zones:
            if min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat:
                return True
        
        return False
    
    def calculate_centroid(self, polygon_coordinates: List[List[float]]) -> Tuple[float, float]:
        """Calcule le centroïde d'un polygone"""
        if not polygon_coordinates:
            raise ValueError("Polygon coordinates cannot be empty")
        
        polygon = Polygon(polygon_coordinates[0])  # Premier ring du polygone
        centroid = polygon.centroid
        return centroid.x, centroid.y
    
    async def enrich_parcelle_data(self, parcel_id: str, geojson_parcelle: Dict) -> Dict[str, Any]:
        """
        Enrichissement complet d'une parcelle cadastrale
        
        Args:
            parcel_id: ID de la parcelle
            geojson_parcelle: Données GeoJSON de la parcelle
            
        Returns:
            Dict contenant toutes les données d'enrichissement IGN
        """
        try:
            logger.info(f"Début enrichissement IGN pour parcelle {parcel_id}")
            
            # Extraction des coordonnées
            coordinates = geojson_parcelle['geometry']['coordinates'][0]
            
            # Calcul du centroïde pour géocodage
            centroid_lon, centroid_lat = self.calculate_centroid(geojson_parcelle['geometry']['coordinates'])
            
            # Enrichissement en parallèle
            tasks = [
                self.get_elevation_profile(coordinates[:10]),  # Limite pour performance
                self.reverse_geocode(centroid_lon, centroid_lat),
                self.get_land_cover(geojson_parcelle['geometry'])
            ]
            
            elevation_data, address_data, land_cover_data = await asyncio.gather(*tasks)
            
            # Compilation des résultats
            enrichment_data = {
                'parcel_id': parcel_id,
                'elevation': elevation_data,
                'address': address_data,
                'land_cover': land_cover_data,
                'geographic_context': {
                    'distance_to_water_m': 1250,  # Simulé pour MVP
                    'distance_to_major_road_m': 89,  # Simulé pour MVP
                    'urban_density': 'dense' if self._is_urban_area(centroid_lon, centroid_lat) else 'sparse',
                    'climate_zone': self._estimate_climate_zone(centroid_lat)
                },
                'enriched_at': timezone.now().isoformat(),
                'data_version': '2024.1'
            }
            
            logger.info(f"Enrichissement IGN terminé pour parcelle {parcel_id}")
            return enrichment_data
            
        except Exception as e:
            logger.error(f"Erreur enrichissement IGN parcelle {parcel_id}: {e}")
            raise IGNServiceError(f"Erreur enrichissement IGN: {e}")
    
    def _estimate_climate_zone(self, latitude: float) -> str:
        """Estimation de la zone climatique basée sur la latitude"""
        if latitude >= 49.5:
            return "Océanique (Cfb)"
        elif latitude >= 47.0:
            return "Océanique dégradé (Cfb)"
        elif latitude >= 44.0:
            return "Continental (Dfb)"
        else:
            return "Méditerranéen (Csa)"
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Retourne le statut du quota IGN"""
        today = timezone.now().date()
        daily_usage = cache.get(f'ign_usage_daily_{today}', 0)
        
        return {
            'daily_usage': daily_usage,
            'daily_quota': self.daily_quota,
            'remaining': max(0, self.daily_quota - daily_usage),
            'percentage_used': round((daily_usage / self.daily_quota) * 100, 1),
            'enabled': self.enabled
        }