from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Project, Parcel, TerrainAnalysis
from .serializers import (
    ProjectSerializer, 
    ProjectListSerializer,
    ParcelSerializer,
    TerrainAnalysisSerializer
)

class ProjectListCreateView(generics.ListCreateAPIView):
    """Liste et création de projets"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProjectListSerializer
        return ProjectSerializer

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un projet"""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_dashboard_stats(request):
    """Statistiques pour le dashboard"""
    user_projects = Project.objects.filter(user=request.user)
    
    stats = {
        'total_projects': user_projects.count(),
        'active_projects': user_projects.filter(
            status__in=['planning', 'design_in_progress']
        ).count(),
        'completed_projects': user_projects.filter(status='completed').count(),
        'total_budget': sum(p.budget_max for p in user_projects if p.budget_max),
    }
    
    # Projets récents
    recent_projects = user_projects.order_by('-updated_at')[:3]
    stats['recent_projects'] = ProjectListSerializer(recent_projects, many=True).data
    
    return Response(stats)

class ParcelListCreateView(generics.ListCreateAPIView):
    """Liste et création de parcelles pour un projet"""
    serializer_class = ParcelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id, user=self.request.user)
        return project.parcels.all()
    
    def perform_create(self, serializer):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id, user=self.request.user)
        serializer.save(project=project)

class ParcelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'une parcelle"""
    serializer_class = ParcelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id, user=self.request.user)
        return project.parcels.all()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_terrain(request, project_id):
    """Analyser le terrain d'un projet"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Créer une analyse de terrain basique
    analysis_data = {
        'project': project.id,
        'soil_type': request.data.get('soil_type', 'unknown'),
        'drainage_quality': request.data.get('drainage_quality', 'medium'),
        'sun_exposure': request.data.get('sun_exposure', 'partial'),
        'slope_percentage': request.data.get('slope_percentage', 0),
        'ph_level': request.data.get('ph_level', 7.0),
        'analysis_notes': request.data.get('analysis_notes', ''),
    }
    
    serializer = TerrainAnalysisSerializer(data=analysis_data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Analyse de terrain créée avec succès',
            'analysis': serializer.data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
