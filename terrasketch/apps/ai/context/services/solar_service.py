"""
Service pour calculer l'orientation solaire et l'ensoleillement d'une parcelle.
"""
import math
from datetime import datetime, timedelta
from pysolar import solar
from typing import Dict, Tuple, List


class SolarService:
    """
    Service pour calculer les données d'ensoleillement d'une parcelle.
    """
    
    @classmethod
    def calculate_solar_orientation(cls, parcelle_geometry: Dict, latitude: float, longitude: float) -> Dict:
        """
        Calcule l'orientation solaire optimale pour une parcelle.
        
        Args:
            parcelle_geometry: Géométrie de la parcelle (GeoJSON)
            latitude: Latitude de la parcelle
            longitude: Longitude de la parcelle
            
        Returns:
            dict: Données d'orientation et d'ensoleillement
        """
        # Calculer l'orientation principale de la parcelle
        main_orientation = cls._calculate_parcel_orientation(parcelle_geometry)
        
        # Calculer les heures de soleil pour différentes périodes
        sun_hours_summer = cls._calculate_daily_sun_hours(latitude, longitude, 6, 21)  # Solstice d'été
        sun_hours_winter = cls._calculate_daily_sun_hours(latitude, longitude, 12, 21)  # Solstice d'hiver
        sun_hours_equinox = cls._calculate_daily_sun_hours(latitude, longitude, 3, 21)  # Équinoxe
        
        # Déterminer le niveau d'ensoleillement
        sun_level = cls._determine_sun_level(sun_hours_summer, latitude)
        
        # Calculer les zones d'ombre approximatives
        shadow_analysis = cls._analyze_shadows(parcelle_geometry, latitude)
        
        return {
            'orientation_principale': main_orientation,
            'heures_soleil_ete': round(sun_hours_summer, 1),
            'heures_soleil_hiver': round(sun_hours_winter, 1),
            'heures_soleil_equinoxe': round(sun_hours_equinox, 1),
            'ensoleillement': sun_level,
            'angle_solaire_max': cls._calculate_max_solar_angle(latitude),
            'zones_ombre': shadow_analysis
        }
    
    @classmethod
    def _calculate_parcel_orientation(cls, geometry: Dict) -> str:
        """
        Calcule l'orientation principale d'une parcelle à partir de sa géométrie.
        
        Analyse les côtés les plus longs pour déterminer l'orientation.
        """
        if not geometry or 'coordinates' not in geometry:
            return "sud-ouest"  # Valeur par défaut
        
        try:
            # Extraire les coordonnées (supposant Polygon)
            coords = geometry['coordinates'][0] if geometry['type'] == 'Polygon' else geometry['coordinates']
            
            if len(coords) < 4:
                return "sud-ouest"
            
            # Calculer les longueurs et orientations des côtés
            sides = []
            for i in range(len(coords) - 1):
                p1 = coords[i]
                p2 = coords[i + 1]
                
                # Calculer la longueur du côté
                length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                
                # Calculer l'angle (orientation)
                angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0]) * 180 / math.pi
                
                sides.append((length, angle))
            
            # Trouver le côté le plus long
            longest_side = max(sides, key=lambda x: x[0])
            angle = longest_side[1]
            
            # Convertir l'angle en orientation cardinale
            return cls._angle_to_cardinal(angle)
            
        except Exception:
            return "sud-ouest"  # Valeur par défaut en cas d'erreur
    
    @classmethod
    def _angle_to_cardinal(cls, angle_deg: float) -> str:
        """
        Convertit un angle en degrés vers une orientation cardinale.
        """
        # Normaliser l'angle entre 0 et 360
        angle = angle_deg % 360
        
        if angle < 22.5 or angle >= 337.5:
            return "est"
        elif angle < 67.5:
            return "nord-est"
        elif angle < 112.5:
            return "nord"
        elif angle < 157.5:
            return "nord-ouest"
        elif angle < 202.5:
            return "ouest"
        elif angle < 247.5:
            return "sud-ouest"
        elif angle < 292.5:
            return "sud"
        else:
            return "sud-est"
    
    @classmethod
    def _calculate_daily_sun_hours(cls, latitude: float, longitude: float, month: int, day: int) -> float:
        """
        Calcule le nombre d'heures de soleil pour une date donnée.
        """
        try:
            date = datetime(2024, month, day, 12, 0, 0)  # Midi, année arbitraire
            
            # Calculer l'heure de lever et coucher du soleil
            sunrise_hour = None
            sunset_hour = None
            
            # Chercher l'heure de lever du soleil (quand l'altitude devient positive)
            for hour in range(24):
                for minute in range(0, 60, 15):  # Par quart d'heure
                    test_date = date.replace(hour=hour, minute=minute)
                    try:
                        altitude = solar.get_altitude(latitude, longitude, test_date)
                        if altitude > 0 and sunrise_hour is None:
                            sunrise_hour = hour + minute/60
                            break
                        elif altitude <= 0 and sunrise_hour is not None and sunset_hour is None:
                            sunset_hour = hour + minute/60
                            break
                    except Exception:
                        continue
                if sunset_hour is not None:
                    break
            
            if sunrise_hour is not None and sunset_hour is not None:
                return max(0, sunset_hour - sunrise_hour)
            else:
                # Valeurs approximatives selon la latitude et la saison
                if month in [6, 7, 8]:  # Été
                    return max(12, 16 - abs(latitude - 46) * 0.1)
                elif month in [12, 1, 2]:  # Hiver
                    return max(6, 10 - abs(latitude - 46) * 0.1)
                else:  # Printemps/Automne
                    return max(9, 12 - abs(latitude - 46) * 0.05)
                
        except Exception:
            # Valeurs par défaut selon la saison
            if month in [6, 7, 8]:  # Été
                return 14.0
            elif month in [12, 1, 2]:  # Hiver
                return 8.0
            else:
                return 11.0
    
    @classmethod
    def _determine_sun_level(cls, summer_sun_hours: float, latitude: float) -> str:
        """
        Détermine le niveau d'ensoleillement.
        """
        if summer_sun_hours > 13:
            return "fort"
        elif summer_sun_hours > 10:
            return "moyen"
        else:
            return "faible"
    
    @classmethod
    def _calculate_max_solar_angle(cls, latitude: float) -> float:
        """
        Calcule l'angle solaire maximum au solstice d'été.
        """
        # Angle de déclinaison solaire au solstice d'été (~23.45°)
        declination = 23.45
        
        # Angle d'élévation solaire maximum = 90° - |latitude - déclinaison|
        max_elevation = 90 - abs(latitude - declination)
        
        return round(max_elevation, 1)
    
    @classmethod
    def _analyze_shadows(cls, geometry: Dict, latitude: float) -> List[Dict]:
        """
        Analyse approximative des zones d'ombre dans la parcelle.
        
        Simplifié : suppose des obstacles standards (bâtiments, arbres).
        """
        shadows = []
        
        # Zone d'ombre approximative au nord (hiver)
        shadows.append({
            "zone": "nord",
            "periode": "hiver",
            "intensite": "forte",
            "description": "Zone moins ensoleillée en hiver, idéale pour plantes d'ombre"
        })
        
        # Zone ensoleillée au sud
        shadows.append({
            "zone": "sud",
            "periode": "toute_annee",
            "intensite": "faible",
            "description": "Zone la plus ensoleillée, idéale pour potager et plantes de soleil"
        })
        
        return shadows
    
    @classmethod
    def get_optimal_zones_placement(cls, solar_data: Dict, parcel_area: float) -> Dict:
        """
        Recommande le placement optimal des zones selon l'ensoleillement.
        """
        orientation = solar_data.get('orientation_principale', 'sud-ouest')
        sun_level = solar_data.get('ensoleillement', 'moyen')
        
        recommendations = {
            'terrasse': {
                'orientation_ideale': 'sud-ouest',
                'justification': 'Profite du soleil d\'après-midi pour les repas'
            },
            'potager': {
                'orientation_ideale': 'sud' if sun_level != 'faible' else 'sud-est',
                'justification': 'Besoin de maximum de soleil pour les légumes'
            },
            'pelouse': {
                'orientation_ideale': 'centre' if sun_level == 'fort' else 'sud',
                'justification': 'Répartie selon l\'ensoleillement disponible'
            },
            'massifs_ombre': {
                'orientation_ideale': 'nord',
                'justification': 'Zone protégée pour plantes d\'ombre'
            },
            'arbre_ombrage': {
                'orientation_ideale': 'ouest',
                'justification': 'Protection contre le soleil d\'après-midi'
            }
        }
        
        return recommendations