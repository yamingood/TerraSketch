from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Plant, PlantFamily, PlantStyle
from .serializers import (
    PlantListSerializer,
    PlantDetailSerializer,
    PlantFamilySerializer,
    PlantStyleSerializer,
    PlantSearchSerializer
)
from .claude_service import ClaudeAIService

class PlantListView(generics.ListAPIView):
    """Liste des plantes avec recherche et filtres"""
    serializer_class = PlantListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Plant.objects.select_related('family').prefetch_related('style_affinities')
        
        # Paramètres de recherche
        search = self.request.query_params.get('search', '')
        family = self.request.query_params.get('family', '')
        style = self.request.query_params.get('style', '')
        sun_requirements = self.request.query_params.get('sun_requirements', '')
        water_needs = self.request.query_params.get('water_needs', '')
        
        # Filtres numériques
        hardiness_zone_min = self.request.query_params.get('hardiness_zone_min', '')
        hardiness_zone_max = self.request.query_params.get('hardiness_zone_max', '')
        height_min = self.request.query_params.get('height_min', '')
        height_max = self.request.query_params.get('height_max', '')
        price_min = self.request.query_params.get('price_min', '')
        price_max = self.request.query_params.get('price_max', '')
        
        # Recherche textuelle
        if search:
            queryset = queryset.filter(
                Q(name_common_fr__icontains=search) |
                Q(name_latin__icontains=search)
            )
        
        # Filtres catégoriels
        if family:
            queryset = queryset.filter(family__name_fr__icontains=family)
        
        if style:
            queryset = queryset.filter(style_affinities__style__icontains=style)
        
        if sun_requirements:
            queryset = queryset.filter(sun_exposure=sun_requirements)
        
        if water_needs:
            queryset = queryset.filter(water_need=water_needs)
        
        # Filtres numériques
        try:
            if hardiness_zone_min:
                queryset = queryset.filter(frost_resistance_min_c__gte=int(hardiness_zone_min))
            if hardiness_zone_max:
                queryset = queryset.filter(frost_resistance_min_c__lte=int(hardiness_zone_max))
            if height_min:
                queryset = queryset.filter(height_adult_max_cm__gte=float(height_min))
            if height_max:
                queryset = queryset.filter(height_adult_max_cm__lte=float(height_max))
        except (ValueError, TypeError):
            pass  # Ignorer les valeurs invalides
        
        return queryset.distinct().order_by('name_common_fr')

class PlantDetailView(generics.RetrieveAPIView):
    """Détails complets d'une plante"""
    queryset = Plant.objects.all()
    serializer_class = PlantDetailSerializer
    permission_classes = [IsAuthenticated]

class PlantFamilyListView(generics.ListAPIView):
    """Liste des familles de plantes"""
    queryset = PlantFamily.objects.all().order_by('name_fr')
    serializer_class = PlantFamilySerializer
    permission_classes = [IsAuthenticated]

class PlantStyleListView(generics.ListAPIView):
    """Liste des styles de plantes"""
    queryset = PlantStyle.objects.all().order_by('style')
    serializer_class = PlantStyleSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plant_recommendations(request, project_id):
    """Recommandations de plantes pour un projet avec IA Claude"""
    try:
        # Récupérer les paramètres de la requête
        criteria = {
            'sun_exposure': request.query_params.get('sun_exposure'),
            'soil_type': request.query_params.get('soil_type'),
            'climate_zone': request.query_params.get('climate_zone'),
            'style': request.query_params.get('style')
        }
        
        # Utiliser le service Claude AI
        claude_service = ClaudeAIService()
        recommendations_data = claude_service.get_plant_recommendations(
            project_id=project_id,
            request_data=criteria
        )
        
        # Sérialiser les plantes recommandées
        serialized_recommendations = []
        for rec in recommendations_data['recommendations']:
            plant_data = PlantListSerializer(rec['plant']).data
            serialized_recommendations.append({
                'plant': plant_data,
                'reasoning': rec['reasoning'],
                'placement_suggestion': rec['placement_suggestion'],
                'maintenance_tips': rec['maintenance_tips']
            })
        
        return Response({
            'project_id': recommendations_data['project_id'],
            'criteria': recommendations_data['criteria'],
            'recommendations': serialized_recommendations,
            'overall_concept': recommendations_data.get('overall_concept', ''),
            'design_principles': recommendations_data.get('design_principles', []),
            'maintenance_calendar': recommendations_data.get('maintenance_calendar', [])
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'project_id': project_id,
            'recommendations': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plant_search_filters(request):
    """Retourne les options disponibles pour les filtres de recherche"""
    families = PlantFamily.objects.values('id', 'name_fr').order_by('name_fr')
    styles = PlantStyle.objects.values('id', 'style').order_by('style')
    
    return Response({
        'families': list(families),
        'styles': list(styles),
        'sun_requirements': [
            {'value': 'full_sun', 'label': 'Plein soleil'},
            {'value': 'partial_shade', 'label': 'Mi-ombre'},
            {'value': 'full_shade', 'label': 'Ombre complète'}
        ],
        'water_needs': [
            {'value': 'low', 'label': 'Faible'},
            {'value': 'medium', 'label': 'Modéré'},
            {'value': 'high', 'label': 'Élevé'}
        ],
        'hardiness_zones': [{'value': i, 'label': f'Zone {i}'} for i in range(1, 12)],
    })
