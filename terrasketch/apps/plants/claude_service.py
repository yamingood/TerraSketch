"""
Service d'intégration Claude API pour les recommandations de plantes
"""
import os
import json
from anthropic import Anthropic
from django.conf import settings
from .models import Plant
from apps.projects.models import Project

class ClaudeAIService:
    def __init__(self):
        # Utiliser la clé API depuis les variables d'environnement
        # Pour la démo, utiliser une simulation
        self.api_key = getattr(settings, 'CLAUDE_API_KEY', None)
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def get_plant_recommendations(self, project_id, request_data):
        """
        Obtenir des recommandations de plantes via Claude AI
        """
        try:
            project = Project.objects.get(id=project_id)
            
            if self.client:
                return self._get_claude_recommendations(project, request_data)
            else:
                # Mode simulation pour la démo
                return self._get_demo_recommendations(project, request_data)
                
        except Project.DoesNotExist:
            raise ValueError(f"Projet {project_id} introuvable")
        except Exception as e:
            raise Exception(f"Erreur lors de la génération des recommandations: {str(e)}")
    
    def _get_claude_recommendations(self, project, request_data):
        """
        Utiliser l'API Claude réelle
        """
        # Récupérer toutes les plantes disponibles
        available_plants = list(Plant.objects.select_related('family').all())
        
        # Construire le prompt pour Claude
        prompt = self._build_claude_prompt(project, request_data, available_plants)
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parser la réponse Claude
            return self._parse_claude_response(response.content[0].text, available_plants)
            
        except Exception as e:
            # En cas d'erreur API, revenir au mode simulation
            return self._get_demo_recommendations(project, request_data)
    
    def _get_demo_recommendations(self, project, request_data):
        """
        Recommandations simulées pour la démo
        """
        # Filtrer les plantes selon les critères
        queryset = Plant.objects.select_related('family').all()
        
        # Appliquer les filtres de base
        sun_exposure = request_data.get('sun_exposure')
        if sun_exposure:
            queryset = queryset.filter(sun_exposure=sun_exposure)
        
        climate_zone = request_data.get('climate_zone')
        if climate_zone:
            queryset = queryset.filter(climate_zones__contains=[climate_zone])
        
        soil_type = request_data.get('soil_type')
        # Note: le filtrage par type de sol nécessiterait des champs additionnels
        
        style = request_data.get('style')
        if style:
            queryset = queryset.filter(style_affinities__style=style)
        
        # Limiter à 8-12 recommandations
        recommended_plants = list(queryset.distinct()[:10])
        
        # Créer des recommandations structurées
        recommendations = []
        for plant in recommended_plants:
            recommendation = {
                'plant': plant,
                'reasoning': self._generate_demo_reasoning(plant, request_data),
                'placement_suggestion': self._generate_placement_suggestion(plant),
                'maintenance_tips': self._generate_maintenance_tips(plant)
            }
            recommendations.append(recommendation)
        
        return {
            'project_id': str(project.id),
            'criteria': request_data,
            'recommendations': recommendations,
            'overall_concept': self._generate_overall_concept(recommended_plants, request_data),
            'design_principles': self._generate_design_principles(request_data),
            'maintenance_calendar': self._generate_maintenance_calendar(recommended_plants)
        }
    
    def _build_claude_prompt(self, project, criteria, available_plants):
        """
        Construire le prompt pour Claude
        """
        plants_data = []
        for plant in available_plants[:50]:  # Limiter pour éviter des prompts trop longs
            plants_data.append({
                'id': str(plant.id),
                'name': plant.name_common_fr,
                'latin': plant.name_latin,
                'family': plant.family.name_fr,
                'height': plant.height_adult_max_cm,
                'sun_exposure': plant.sun_exposure,
                'water_need': plant.water_need,
                'frost_resistance': plant.frost_resistance_min_c,
                'type': plant.type
            })
        
        prompt = f"""
        Tu es un expert paysagiste qui aide à créer des recommandations de plantes pour un projet d'aménagement.

        PROJET:
        - Nom: {project.name}
        - Localisation: {project.city or 'Non spécifiée'}
        - Budget: {project.budget_tier or 'Non spécifié'}

        CRITÈRES DEMANDÉS:
        - Exposition solaire: {criteria.get('sun_exposure', 'Non spécifiée')}
        - Type de sol: {criteria.get('soil_type', 'Non spécifié')}
        - Zone climatique: {criteria.get('climate_zone', 'Non spécifiée')}
        - Style souhaité: {criteria.get('style', 'Non spécifié')}

        PLANTES DISPONIBLES:
        {json.dumps(plants_data, ensure_ascii=False, indent=2)}

        MISSION:
        Recommande 6-10 plantes parmi celles disponibles qui correspondent aux critères.
        Pour chaque plante recommandée, fournis:
        1. L'ID de la plante
        2. Une explication du choix (2-3 phrases)
        3. Une suggestion de placement
        4. Des conseils d'entretien

        Réponds en JSON avec cette structure:
        {{
            "recommendations": [
                {{
                    "plant_id": "uuid",
                    "reasoning": "text",
                    "placement_suggestion": "text", 
                    "maintenance_tips": "text"
                }}
            ],
            "overall_concept": "text",
            "design_principles": ["principe1", "principe2"]
        }}
        """
        
        return prompt
    
    def _parse_claude_response(self, response_text, available_plants):
        """
        Parser la réponse JSON de Claude
        """
        try:
            data = json.loads(response_text)
            
            # Convertir les IDs en objets Plant
            recommendations = []
            for rec in data.get('recommendations', []):
                plant_id = rec.get('plant_id')
                plant = next((p for p in available_plants if str(p.id) == plant_id), None)
                
                if plant:
                    recommendations.append({
                        'plant': plant,
                        'reasoning': rec.get('reasoning', ''),
                        'placement_suggestion': rec.get('placement_suggestion', ''),
                        'maintenance_tips': rec.get('maintenance_tips', '')
                    })
            
            return {
                'recommendations': recommendations,
                'overall_concept': data.get('overall_concept', ''),
                'design_principles': data.get('design_principles', []),
                'maintenance_calendar': self._generate_maintenance_calendar([r['plant'] for r in recommendations])
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            # En cas d'erreur de parsing, revenir au mode démo
            raise Exception(f"Erreur de parsing de la réponse Claude: {str(e)}")
    
    def _generate_demo_reasoning(self, plant, criteria):
        """Générer un raisonnement pour la démo"""
        reasons = []
        
        if criteria.get('sun_exposure') == plant.sun_exposure:
            exposure_names = {
                'full_sun': 'plein soleil',
                'partial_shade': 'mi-ombre',
                'full_shade': 'ombre'
            }
            reasons.append(f"Parfaite pour une exposition {exposure_names.get(plant.sun_exposure, plant.sun_exposure)}")
        
        if plant.is_drought_resistant:
            reasons.append("Résistante à la sécheresse, idéale pour un entretien facile")
        
        if plant.attracts_pollinators:
            reasons.append("Attire les pollinisateurs, contribue à la biodiversité")
        
        if not reasons:
            reasons.append(f"Excellente plante de la famille des {plant.family.name_fr}")
        
        return ". ".join(reasons[:2]) + "."
    
    def _generate_placement_suggestion(self, plant):
        """Générer une suggestion de placement"""
        suggestions = {
            'tree': "À placer en arrière-plan ou en point focal",
            'shrub': "Parfait pour structurer les massifs",
            'perennial': "Idéale en bordure ou en masse",
            'groundcover': "Excellent couvre-sol pour les zones difficiles",
            'climber': "Parfait contre un mur ou une pergola"
        }
        
        base_suggestion = suggestions.get(plant.type, "À intégrer dans la composition")
        
        if plant.height_adult_max_cm > 200:
            return f"{base_suggestion}, attention à l'espace nécessaire ({plant.height_adult_max_cm}cm à maturité)"
        
        return base_suggestion
    
    def _generate_maintenance_tips(self, plant):
        """Générer des conseils d'entretien"""
        tips = []
        
        water_names = {
            'low': 'Arrosage modéré, résiste bien à la sécheresse',
            'moderate': 'Arrosage régulier pendant la croissance',
            'high': 'Nécessite un sol toujours frais'
        }
        
        tips.append(water_names.get(plant.water_need, 'Arrosage selon les conditions'))
        
        if plant.frost_resistance_min_c < -10:
            tips.append("Très rustique, résiste aux gelées fortes")
        elif plant.frost_resistance_min_c < 0:
            tips.append("Rustique, supporte les gelées légères")
        else:
            tips.append("Sensible au gel, protéger en hiver")
        
        return ". ".join(tips) + "."
    
    def _generate_overall_concept(self, plants, criteria):
        """Générer un concept général"""
        style = criteria.get('style', '')
        
        if 'méditerranéen' in style.lower():
            return "Jardin méditerranéen avec des plantes résistantes à la sécheresse et aux couleurs chaudes"
        elif 'moderne' in style.lower():
            return "Design contemporain avec des lignes épurées et des plantes architecturales"
        elif 'naturel' in style.lower():
            return "Aménagement naturel favorisant la biodiversité et l'écosystème local"
        
        return "Composition harmonieuse adaptée au climat et aux conditions du site"
    
    def _generate_design_principles(self, criteria):
        """Générer les principes de design"""
        principles = ["Adaptation au climat local", "Facilité d'entretien"]
        
        sun_exposure = criteria.get('sun_exposure')
        if sun_exposure == 'full_sun':
            principles.append("Optimisation de l'exposition ensoleillée")
        elif sun_exposure == 'full_shade':
            principles.append("Valorisation des zones ombragées")
        
        if criteria.get('style'):
            principles.append(f"Cohérence stylistique {criteria['style']}")
        
        principles.append("Échelonnement des floraisons")
        
        return principles
    
    def _generate_maintenance_calendar(self, plants):
        """Générer un calendrier d'entretien"""
        calendar = [
            {"month": 3, "tasks": ["Taille des arbustes", "Premier apport d'engrais"]},
            {"month": 4, "tasks": ["Plantation des nouvelles espèces", "Division des vivaces"]},
            {"month": 5, "tasks": ["Paillage des massifs", "Surveillance des ravageurs"]},
            {"month": 6, "tasks": ["Arrosage régulier", "Suppression des fleurs fanées"]},
            {"month": 9, "tasks": ["Plantation d'automne", "Nettoyage des massifs"]},
            {"month": 11, "tasks": ["Protection hivernale", "Dernière tonte"]}
        ]
        
        return calendar