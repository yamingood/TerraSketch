"""
Service pour sélectionner les plantes compatibles avec les conditions climatiques et le projet.
"""
from typing import List, Dict, Optional
from django.db.models import Q
from ...models import PlantCompatibility
from apps.plants.models import Plant


class PlantSelector:
    """
    Service pour sélectionner les plantes adaptées aux conditions du projet.
    """
    
    @classmethod
    def select_compatible_plants(
        cls,
        zone_climatique: str,
        zone_rusticite: str,
        stress_hydrique: str,
        preferences: Dict,
        max_plants: int = 40
    ) -> List[Dict]:
        """
        Sélectionne les plantes compatibles selon les critères climatiques et les préférences.
        
        Args:
            zone_climatique: "Atlantique", "Continental", "Méditerranéen", "Montagnard"
            zone_rusticite: "Z6b", "Z7a", "Z7b", "Z8a", "Z8b", "Z9a", "Z9b"
            stress_hydrique: "faible", "modere", "fort"
            preferences: Préférences utilisateur (style, usages, plantes souhaitées, etc.)
            max_plants: Nombre maximum de plantes à retourner
            
        Returns:
            List[Dict]: Liste des plantes avec leurs données complètes
        """
        # Récupérer les plantes depuis le cache de compatibilité
        compatible_plants = cls._get_compatible_from_cache(
            zone_climatique, zone_rusticite, stress_hydrique
        )
        
        if not compatible_plants:
            # Si pas de cache, calculer la compatibilité
            compatible_plants = cls._calculate_plant_compatibility(
                zone_climatique, zone_rusticite, stress_hydrique
            )
        
        # Filtrer selon les préférences utilisateur
        filtered_plants = cls._filter_by_preferences(compatible_plants, preferences)
        
        # Limiter le nombre et retourner avec les données complètes
        selected_plants = filtered_plants[:max_plants]
        
        return cls._format_plants_for_ai(selected_plants)
    
    @classmethod
    def _get_compatible_from_cache(
        cls, zone_climatique: str, zone_rusticite: str, stress_hydrique: str
    ) -> List[Plant]:
        """
        Récupère les plantes compatibles depuis le cache.
        """
        try:
            compatibility_entries = PlantCompatibility.objects.filter(
                zone_climatique=zone_climatique,
                zone_rusticite=zone_rusticite,
                stress_hydrique=stress_hydrique,
                is_compatible=True
            ).select_related('plant').order_by('-compatibility_score')
            
            return [entry.plant for entry in compatibility_entries]
        except Exception:
            return []
    
    @classmethod
    def _calculate_plant_compatibility(
        cls, zone_climatique: str, zone_rusticite: str, stress_hydrique: str
    ) -> List[Plant]:
        """
        Calcule la compatibilité des plantes et met en cache.
        """
        # Récupérer toutes les plantes
        all_plants = Plant.objects.all()
        compatible_plants = []
        
        for plant in all_plants:
            score = cls._calculate_compatibility_score(
                plant, zone_climatique, zone_rusticite, stress_hydrique
            )
            
            is_compatible = score >= 50  # Seuil de compatibilité
            
            # Sauvegarder en cache
            PlantCompatibility.objects.update_or_create(
                plant=plant,
                zone_climatique=zone_climatique,
                zone_rusticite=zone_rusticite,
                stress_hydrique=stress_hydrique,
                defaults={
                    'is_compatible': is_compatible,
                    'compatibility_score': score
                }
            )
            
            if is_compatible:
                compatible_plants.append(plant)
        
        return compatible_plants
    
    @classmethod
    def _calculate_compatibility_score(
        cls, plant: Plant, zone_climatique: str, zone_rusticite: str, stress_hydrique: str
    ) -> float:
        """
        Calcule un score de compatibilité pour une plante (0-100).
        """
        score = 50  # Score de base
        
        # Vérifier la zone climatique (très important)
        if hasattr(plant, 'climate_zones') and plant.climate_zones:
            if zone_climatique.lower() in plant.climate_zones.lower():
                score += 25
            else:
                score -= 15
        
        # Vérifier la rusticité (critique)
        if hasattr(plant, 'hardiness_zone') and plant.hardiness_zone:
            plant_zone = plant.hardiness_zone.replace('Z', '').replace('z', '')
            current_zone = zone_rusticite.replace('Z', '').replace('z', '')
            
            try:
                # Comparer les zones de rusticité (Z8a vs Z8b, etc.)
                if plant_zone <= current_zone:
                    score += 20
                else:
                    score -= 30  # Plante pas assez rustique
            except Exception:
                pass  # Zone mal formatée, pas de bonus/malus
        
        # Vérifier les besoins en eau
        if hasattr(plant, 'water_needs') and plant.water_needs:
            if stress_hydrique == "faible":
                if "sèche" in plant.water_needs.lower() or "faible" in plant.water_needs.lower():
                    score += 15
                elif "humide" in plant.water_needs.lower():
                    score -= 10
            elif stress_hydrique == "fort":
                if "humide" in plant.water_needs.lower() or "fraîche" in plant.water_needs.lower():
                    score += 15
                elif "sèche" in plant.water_needs.lower():
                    score -= 10
        
        # Bonus pour les plantes natives françaises
        if hasattr(plant, 'is_native') and plant.is_native:
            score += 10
        
        # Bonus pour les plantes faciles d'entretien
        if hasattr(plant, 'maintenance_level') and plant.maintenance_level:
            if "faible" in plant.maintenance_level.lower() or "facile" in plant.maintenance_level.lower():
                score += 5
        
        return max(0, min(100, score))  # Limiter entre 0 et 100
    
    @classmethod
    def _filter_by_preferences(cls, plants: List[Plant], preferences: Dict) -> List[Plant]:
        """
        Filtre les plantes selon les préférences utilisateur.
        """
        filtered = list(plants)  # Copie
        
        # Filtrer par style de jardin
        style = preferences.get('style', '')
        if style:
            style_plants = []
            for plant in filtered:
                if cls._matches_style(plant, style):
                    style_plants.append(plant)
            if style_plants:  # Si des plantes correspondent au style, privilégier celles-ci
                filtered = style_plants
        
        # Filtrer par niveau d'entretien souhaité
        entretien = preferences.get('niveau_entretien', '')
        if entretien == 'faible':
            filtered = [p for p in filtered if cls._is_low_maintenance(p)]
        
        # Inclure les plantes spécifiquement demandées
        plantes_souhaitees = preferences.get('plantes_souhaitees', [])
        if plantes_souhaitees:
            for plant_name in plantes_souhaitees:
                matching_plants = Plant.objects.filter(
                    Q(name_common__icontains=plant_name) | 
                    Q(name_latin__icontains=plant_name)
                )
                for plant in matching_plants:
                    if plant not in filtered:
                        filtered.append(plant)
        
        # Filtrer les plantes toxiques si il y a des animaux/enfants
        if preferences.get('enfants') or preferences.get('animaux'):
            filtered = [p for p in filtered if not cls._is_toxic(p)]
        
        # Inclure des fruitiers si demandé
        if preferences.get('fruitiers'):
            fruit_plants = Plant.objects.filter(category__name__icontains='fruitier')
            for plant in fruit_plants:
                if plant not in filtered:
                    filtered.append(plant)
        
        return filtered
    
    @classmethod
    def _matches_style(cls, plant: Plant, style: str) -> bool:
        """
        Vérifie si une plante correspond au style de jardin.
        """
        style_lower = style.lower()
        
        if not hasattr(plant, 'garden_styles') or not plant.garden_styles:
            return True  # Pas d'info, on garde la plante
        
        styles_lower = plant.garden_styles.lower()
        
        style_mapping = {
            'mediterraneen': ['méditerranéen', 'sec', 'provence'],
            'japonais': ['japonais', 'zen', 'asiatique'],
            'contemporain': ['moderne', 'contemporain', 'architectural'],
            'classique': ['classique', 'français', 'traditionnel'],
            'naturel': ['naturel', 'sauvage', 'prairie', 'champêtre']
        }
        
        keywords = style_mapping.get(style_lower, [style_lower])
        
        return any(keyword in styles_lower for keyword in keywords)
    
    @classmethod
    def _is_low_maintenance(cls, plant: Plant) -> bool:
        """
        Vérifie si une plante est facile d'entretien.
        """
        if hasattr(plant, 'maintenance_level') and plant.maintenance_level:
            maintenance = plant.maintenance_level.lower()
            return any(word in maintenance for word in ['faible', 'facile', 'minimal', 'sans'])
        
        # Plantes généralement faciles (heuristiques)
        if hasattr(plant, 'name_common') and plant.name_common:
            easy_plants = ['lavande', 'romarin', 'thym', 'sedum', 'graminée', 'lierre']
            name_lower = plant.name_common.lower()
            return any(easy in name_lower for easy in easy_plants)
        
        return True  # Par défaut, on considère la plante comme acceptable
    
    @classmethod
    def _is_toxic(cls, plant: Plant) -> bool:
        """
        Vérifie si une plante est toxique.
        """
        if hasattr(plant, 'toxicity') and plant.toxicity:
            toxicity = plant.toxicity.lower()
            return 'toxique' in toxicity or 'poison' in toxicity
        
        # Liste de plantes connues comme toxiques
        if hasattr(plant, 'name_latin') and plant.name_latin:
            toxic_plants = ['oleander', 'ricinus', 'taxus', 'digitalis', 'aconitum']
            name_lower = plant.name_latin.lower()
            return any(toxic in name_lower for toxic in toxic_plants)
        
        return False  # Par défaut, on considère la plante comme sûre
    
    @classmethod
    def _format_plants_for_ai(cls, plants: List[Plant]) -> List[Dict]:
        """
        Formate les plantes pour l'injection dans le prompt AI.
        
        Format optimisé pour réduire les tokens tout en gardant les infos essentielles.
        """
        formatted_plants = []
        
        for plant in plants:
            plant_data = {
                'name_latin': plant.name_latin,
                'name_common': plant.name_common,
                'category': getattr(plant.category, 'name', 'Autre') if hasattr(plant, 'category') and plant.category else 'Autre',
                'height_max': getattr(plant, 'height_max_cm', 100),
                'width_max': getattr(plant, 'width_max_cm', 100),
                'bloom_period': getattr(plant, 'bloom_period', ''),
                'foliage_type': getattr(plant, 'foliage_type', ''),
                'sun_requirement': getattr(plant, 'sun_requirement', 'soleil'),
                'water_needs': getattr(plant, 'water_needs', 'modéré'),
                'soil_type': getattr(plant, 'soil_type', 'tous'),
                'growth_speed': getattr(plant, 'growth_speed', 'moyen'),
                'maintenance_level': getattr(plant, 'maintenance_level', 'moyen'),
                'hardiness_zone': getattr(plant, 'hardiness_zone', 'Z8'),
                'is_native': getattr(plant, 'is_native', False),
                'price_range': getattr(plant, 'price_range', 'moyen')
            }
            
            formatted_plants.append(plant_data)
        
        return formatted_plants
    
    @classmethod
    def get_plant_suggestions_by_usage(cls, usage: str, plants: List[Dict]) -> List[Dict]:
        """
        Suggère des plantes spécifiques selon l'usage (haie, massif, potager, etc.).
        """
        usage_mapping = {
            'haie': ['arbuste', 'conifère', 'persistant'],
            'massif': ['vivace', 'annuelle', 'bulbe'],
            'potager': ['légume', 'aromatique', 'fruitier'],
            'couvre_sol': ['tapissante', 'rampante', 'couvre-sol'],
            'grimpante': ['grimpante', 'volubile'],
            'arbre': ['arbre', 'grand_développement']
        }
        
        keywords = usage_mapping.get(usage, [])
        if not keywords:
            return plants
        
        suggested = []
        for plant in plants:
            category = plant.get('category', '').lower()
            foliage = plant.get('foliage_type', '').lower()
            
            if any(keyword in category or keyword in foliage for keyword in keywords):
                suggested.append(plant)
        
        return suggested if suggested else plants[:10]  # Fallback si aucune correspondance