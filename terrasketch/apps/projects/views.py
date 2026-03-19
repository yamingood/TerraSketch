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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_plan(request, project_id):
    """
    POST /api/projects/{project_id}/generate/
    
    Déclenche la génération d'un plan paysager par IA pour le projet.
    
    Body:
    {
        "preferences": {
            "style": "moderne",
            "budget_category": "medium",
            "maintenance_level": "low",
            "plant_types": ["arbustes", "vivaces"],
            "color_preferences": ["vert", "blanc"],
            "special_requests": "Zone détente avec banc"
        },
        "force_regenerate": false
    }
    
    Response (201):
    {
        "generation_job_id": "uuid",
        "status": "started",
        "estimated_duration": "2-3 minutes",
        "message": "Génération en cours...",
        "websocket_url": "wss://api.terrasketch.com/ws/generation/{job_id}/"
    }
    
    Response (429) - Rate limit:
    {
        "error": "Limite de génération atteinte",
        "quota_remaining": 0,
        "reset_time": "2024-01-20T15:30:00Z"
    }
    """
    import json
    import logging
    from django.utils import timezone
    from datetime import timedelta
    
    # Import des services IA
    try:
        from apps.ai.models import GenerationJob, UserGenerationQuota
        from apps.ai.context.context_assembler import ContextAssembler
        from apps.ai.prompt.builder import PromptBuilder
        from apps.ai.generator.claude_client import ClaudeClient
    except ImportError as e:
        return Response({
            "error": "Module IA non disponible",
            "detail": str(e),
            "suggestion": "Contactez l'équipe technique"
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    logger = logging.getLogger(__name__)
    
    # Récupération du projet
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Validation données entrée
    preferences = request.data.get('preferences', {})
    force_regenerate = request.data.get('force_regenerate', False)
    
    # Validation préférences basiques
    valid_styles = ['moderne', 'classique', 'naturel', 'zen', 'tropical']
    valid_budgets = ['low', 'medium', 'high']
    valid_maintenance = ['low', 'medium', 'high']
    
    style = preferences.get('style', 'moderne')
    if style not in valid_styles:
        return Response({
            "error": f"Style '{style}' non supporté",
            "valid_styles": valid_styles
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérification quota utilisateur
    quota, created = UserGenerationQuota.objects.get_or_create(
        user=request.user,
        defaults={'generations_used': 0, 'last_reset': timezone.now()}
    )
    
    # Reset quota si nécessaire (daily reset)
    if timezone.now() - quota.last_reset > timedelta(days=1):
        quota.generations_used = 0
        quota.last_reset = timezone.now()
        quota.save()
    
    # Vérification limite quotidienne
    from django.conf import settings
    daily_limit = getattr(settings, 'GENERATION_RATE_LIMIT_PER_USER', 3)
    
    if quota.generations_used >= daily_limit and not force_regenerate:
        return Response({
            "error": "Limite de génération quotidienne atteinte",
            "quota_used": quota.generations_used,
            "quota_limit": daily_limit,
            "reset_time": (quota.last_reset + timedelta(days=1)).isoformat(),
            "suggestion": "Réessayez demain ou contactez-nous pour augmenter votre quota"
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Vérification projet a des données géographiques
    if not project.parcels.exists():
        return Response({
            "error": "Aucune parcelle définie pour ce projet",
            "suggestion": "Uploadez d'abord un fichier cadastral ou définissez la géométrie"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Création du job de génération
        generation_job = GenerationJob.objects.create(
            project=project,
            user=request.user,
            preferences=preferences,
            status='queued'
        )
        
        # Assemblage du contexte
        logger.info(f"Début génération plan IA - Project: {project_id}, Job: {generation_job.id}")
        
        context_assembler = ContextAssembler()
        
        # Récupération première parcelle (MVP - une seule parcelle par projet)
        main_parcel = project.parcels.first()
        
        context_data = context_assembler.assemble_full_context(
            geometry=main_parcel.geometry,
            latitude=main_parcel.latitude,
            longitude=main_parcel.longitude,
            user_preferences=preferences
        )
        
        # Mise à jour job avec contexte
        generation_job.context_data = context_data
        generation_job.status = 'context_ready'
        generation_job.save()
        
        # Construction du prompt
        prompt_builder = PromptBuilder()
        system_prompt, user_prompt = prompt_builder.build_generation_prompts(
            context_data, preferences
        )
        
        generation_job.system_prompt = system_prompt
        generation_job.user_prompt = user_prompt
        generation_job.status = 'prompt_ready'
        generation_job.save()
        
        # Estimation durée
        prompt_tokens = len(user_prompt) // 4  # Approximation tokens
        estimated_seconds = min(max(prompt_tokens // 50, 30), 180)  # 30s-3min
        
        # Réponse immédiate avec job ID
        response_data = {
            "generation_job_id": str(generation_job.id),
            "status": "queued",
            "estimated_duration_seconds": estimated_seconds,
            "estimated_duration": f"{estimated_seconds//60}m{estimated_seconds%60}s",
            "message": "Génération en cours d'initialisation...",
            "project_id": project_id,
            "style": style,
            "created_at": generation_job.created_at.isoformat()
        }
        
        # Déclencher génération asynchrone (Phase 2 - avec Celery)
        # TODO: Implémenter tâche Celery pour génération complète
        # generate_plan_task.delay(generation_job.id)
        
        # Pour MVP - générer de manière synchrone (simple)
        try:
            # Test basique du client Claude (sans génération complète pour MVP)
            claude_client = ClaudeClient()
            
            # Mise à jour quota
            quota.generations_used += 1
            quota.save()
            
            generation_job.status = 'in_progress'
            generation_job.started_at = timezone.now()
            generation_job.save()
            
            logger.info(f"Génération démarrée - Job: {generation_job.id}")
            
        except Exception as e:
            generation_job.status = 'failed'
            generation_job.error_message = str(e)
            generation_job.save()
            
            logger.error(f"Erreur génération IA Job {generation_job.id}: {e}")
            
            return Response({
                "error": "Erreur lors du démarrage de la génération",
                "job_id": str(generation_job.id),
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erreur création job génération Project {project_id}: {e}")
        
        return Response({
            "error": "Erreur interne lors de la création du job",
            "detail": str(e),
            "suggestion": "Réessayez ou contactez le support"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generation_status(request, project_id, job_id):
    """
    GET /api/projects/{project_id}/generate/{job_id}/
    
    Récupère le statut d'une génération en cours.
    """
    from apps.ai.models import GenerationJob
    
    project = get_object_or_404(Project, id=project_id, user=request.user)
    job = get_object_or_404(GenerationJob, id=job_id, project=project, user=request.user)
    
    response_data = {
        "job_id": str(job.id),
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "progress_percentage": job.progress_percentage,
        "current_step": job.current_step,
        "error_message": job.error_message
    }
    
    # Ajouter le plan si terminé
    if job.status == 'completed' and job.plan:
        response_data["plan_id"] = str(job.plan.id)
        response_data["plan_url"] = f"/api/projects/{project_id}/plans/{job.plan.id}/"
    
    return Response(response_data)
