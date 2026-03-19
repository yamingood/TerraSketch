"""
Service pour récupérer et traiter les données climatiques via Open-Meteo.
"""
import httpx
from typing import Dict, Optional
from django.utils import timezone
from datetime import timedelta
from ...models import ClimateCache


class ClimateService:
    """
    Service pour récupérer les données climatiques depuis Open-Meteo API.
    """
    
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    
    @classmethod
    def get_climate_data(cls, latitude: float, longitude: float) -> Dict:
        """
        Récupère les données climatiques pour une position donnée.
        
        Utilise le cache si disponible et non expiré.
        Sinon, appelle l'API Open-Meteo et met en cache.
        
        Args:
            latitude: Latitude de la parcelle
            longitude: Longitude de la parcelle
            
        Returns:
            dict: Données climatiques complètes
        """
        # Vérifier le cache
        try:
            cache_entry = ClimateCache.objects.get(
                latitude=round(latitude, 4),  # Arrondir pour le cache
                longitude=round(longitude, 4)
            )
            if not cache_entry.is_expired:
                return cache_entry.data
        except ClimateCache.DoesNotExist:
            pass
        
        # Appeler l'API Open-Meteo
        climate_data = cls._fetch_from_api(latitude, longitude)
        
        # Mettre en cache
        cache_entry, created = ClimateCache.objects.update_or_create(
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            defaults={'data': climate_data}
        )
        
        return climate_data
    
    @classmethod
    def _fetch_from_api(cls, latitude: float, longitude: float) -> Dict:
        """
        Récupère les données depuis l'API Open-Meteo.
        
        Paramètres récupérés :
        - Température moyenne annuelle
        - Température minimale record
        - Précipitations annuelles
        - Nombre de jours de gel
        - Évapotranspiration
        """
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'daily': [
                'temperature_2m_mean',
                'temperature_2m_min',
                'precipitation_sum',
                'et0_fao_evapotranspiration'
            ],
            'timezone': 'Europe/Paris',
            'past_days': 365,  # Données sur 1 an
            'forecast_days': 0
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(cls.OPEN_METEO_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Traiter les données pour extraire les moyennes annuelles
                return cls._process_climate_data(data)
                
        except Exception as e:
            # En cas d'erreur API, retourner des valeurs par défaut
            return cls._get_fallback_climate_data(latitude, longitude)
    
    @classmethod
    def _process_climate_data(cls, raw_data: Dict) -> Dict:
        """
        Traite les données brutes de l'API pour calculer les moyennes.
        """
        daily_data = raw_data.get('daily', {})
        
        # Températures
        temp_means = daily_data.get('temperature_2m_mean', [])
        temp_mins = daily_data.get('temperature_2m_min', [])
        
        # Précipitations et évapotranspiration
        precipitations = daily_data.get('precipitation_sum', [])
        evapotranspiration = daily_data.get('et0_fao_evapotranspiration', [])
        
        # Calculer les moyennes (filtrer les valeurs None)
        valid_temps = [t for t in temp_means if t is not None]
        valid_temp_mins = [t for t in temp_mins if t is not None]
        valid_precip = [p for p in precipitations if p is not None]
        valid_eto = [e for e in evapotranspiration if e is not None]
        
        temp_moyenne = sum(valid_temps) / len(valid_temps) if valid_temps else 12.0
        temp_min_record = min(valid_temp_mins) if valid_temp_mins else -5.0
        precip_annuelles = sum(valid_precip) if valid_precip else 800.0
        eto_annuelle = sum(valid_eto) if valid_eto else 800.0
        
        # Calculer le nombre de jours de gel
        jours_gel = len([t for t in valid_temp_mins if t < 0])
        
        # Calculer le stress hydrique
        stress_hydrique = cls._calculate_water_stress(precip_annuelles, eto_annuelle)
        
        return {
            'temperature_moy_annuelle': round(temp_moyenne, 1),
            'temperature_minimale_record': round(temp_min_record, 1),
            'precipitations_annuelles': round(precip_annuelles, 0),
            'evapotranspiration_annuelle': round(eto_annuelle, 0),
            'jours_gel_par_an': jours_gel,
            'stress_hydrique': stress_hydrique,
            'fetched_at': timezone.now().isoformat()
        }
    
    @classmethod
    def _calculate_water_stress(cls, precipitations: float, evapotranspiration: float) -> str:
        """
        Calcule le niveau de stress hydrique.
        
        Basé sur le ratio précipitations / évapotranspiration :
        - ratio < 0.6  → "faible"
        - ratio 0.6-1  → "modere"
        - ratio > 1    → "fort"
        """
        if evapotranspiration == 0:
            return "modere"
            
        ratio = precipitations / evapotranspiration
        
        if ratio < 0.6:
            return "faible"
        elif ratio <= 1.0:
            return "modere"
        else:
            return "fort"
    
    @classmethod
    def _get_fallback_climate_data(cls, latitude: float, longitude: float) -> Dict:
        """
        Données climatiques par défaut en cas d'erreur API.
        
        Estimations basées sur la position géographique française.
        """
        # Estimation basée sur la latitude (France métropolitaine)
        if latitude > 49:  # Nord de la France
            zone_climatique = "Continental"
            temp_moy = 10.5
            precip = 650
            jours_gel = 45
        elif latitude > 45:  # Centre de la France
            zone_climatique = "Continental"
            temp_moy = 12.0
            precip = 750
            jours_gel = 25
        elif longitude < 3:  # Côte Atlantique
            zone_climatique = "Atlantique"
            temp_moy = 13.5
            precip = 900
            jours_gel = 15
        else:  # Sud/Est
            zone_climatique = "Méditerranéen"
            temp_moy = 15.0
            precip = 600
            jours_gel = 5
        
        return {
            'temperature_moy_annuelle': temp_moy,
            'temperature_minimale_record': -7.0,
            'precipitations_annuelles': precip,
            'evapotranspiration_annuelle': 800.0,
            'jours_gel_par_an': jours_gel,
            'stress_hydrique': "modere",
            'zone_climatique_estimee': zone_climatique,
            'fallback': True,
            'fetched_at': timezone.now().isoformat()
        }
    
    @classmethod
    def determine_climate_zone(cls, latitude: float, longitude: float, climate_data: Dict) -> str:
        """
        Détermine la zone climatique française à partir des données.
        
        Returns:
            str: "Atlantique", "Continental", "Méditerranéen", "Montagnard", ou "Tropical"
        """
        temp_moy = climate_data.get('temperature_moy_annuelle', 12.0)
        precip = climate_data.get('precipitations_annuelles', 750.0)
        
        # Logique de détermination de zone climatique
        if temp_moy > 24 and precip > 1500:  # DOM-TOM tropicaux
            return "Tropical"
        elif latitude > 49:  # Nord
            return "Continental"
        elif latitude < 43.5:  # Sud
            if precip < 700:
                return "Méditerranéen"
            else:
                return "Atlantique"
        elif longitude < 2:  # Côte Ouest
            return "Atlantique"
        elif temp_moy < 10:  # Altitude ou montagne
            return "Montagnard"
        else:
            return "Continental"
    
    @classmethod
    def determine_hardiness_zone(cls, temp_min_record: float) -> str:
        """
        Détermine la zone de rusticité USDA adaptée à la France.
        
        Args:
            temp_min_record: Température minimale record en °C
            
        Returns:
            str: Zone de rusticité (ex: "Z8a", "Z8b", "Z9a")
        """
        if temp_min_record <= -15:
            return "Z6b"
        elif temp_min_record <= -12:
            return "Z7a"
        elif temp_min_record <= -9:
            return "Z7b"
        elif temp_min_record <= -7:
            return "Z8a"
        elif temp_min_record <= -4:
            return "Z8b"
        elif temp_min_record <= -1:
            return "Z9a"
        else:
            return "Z9b"