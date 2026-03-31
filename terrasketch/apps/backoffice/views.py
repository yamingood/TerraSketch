from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, Subscription
from apps.projects.models import Project
from apps.ai.models import GenerationJob
from .serializers import (
    AdminUserSerializer,
    AdminProjectSerializer,
    AdminGenerationJobSerializer,
)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """Vue d'ensemble des statistiques admin."""
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    total_users = User.objects.count()
    new_users_30d = User.objects.filter(created_at__gte=last_30_days).count()
    new_users_7d = User.objects.filter(created_at__gte=last_7_days).count()
    users_by_role = dict(
        User.objects.values_list('role').annotate(c=Count('id')).values_list('role', 'c')
    )

    active_subs = Subscription.objects.filter(status='active').count()
    trialing_subs = Subscription.objects.filter(status='trialing').count()
    subs_by_plan = dict(
        Subscription.objects.values_list('plan').annotate(c=Count('id')).values_list('plan', 'c')
    )

    total_projects = Project.objects.count()
    new_projects_30d = Project.objects.filter(created_at__gte=last_30_days).count()
    projects_by_status = dict(
        Project.objects.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
    )

    total_jobs = GenerationJob.objects.count()
    jobs_completed = GenerationJob.objects.filter(status='completed').count()
    jobs_failed = GenerationJob.objects.filter(status='failed').count()
    jobs_running = GenerationJob.objects.filter(status='running').count()
    jobs_30d = GenerationJob.objects.filter(created_at__gte=last_30_days).count()
    success_rate = round(jobs_completed / total_jobs * 100, 1) if total_jobs > 0 else 0

    return Response({
        'users': {
            'total': total_users,
            'new_7d': new_users_7d,
            'new_30d': new_users_30d,
            'by_role': users_by_role,
        },
        'subscriptions': {
            'active': active_subs,
            'trialing': trialing_subs,
            'by_plan': subs_by_plan,
        },
        'projects': {
            'total': total_projects,
            'new_30d': new_projects_30d,
            'by_status': projects_by_status,
        },
        'ai_generation': {
            'total_jobs': total_jobs,
            'completed': jobs_completed,
            'failed': jobs_failed,
            'running': jobs_running,
            'jobs_30d': jobs_30d,
            'success_rate': success_rate,
        },
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_users_list(request):
    """Liste paginée des utilisateurs avec filtres."""
    search = request.query_params.get('search', '').strip()
    role = request.query_params.get('role', '').strip()

    qs = User.objects.select_related('subscription').prefetch_related('projects')

    if search:
        qs = qs.filter(email__icontains=search) | qs.filter(first_name__icontains=search) | qs.filter(last_name__icontains=search)
    if role:
        qs = qs.filter(role=role)

    qs = qs.order_by('-created_at')[:200]
    return Response(AdminUserSerializer(qs, many=True).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_user_update(request, user_id):
    """Modifier le rôle ou le statut d'un utilisateur."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

    allowed = {'role', 'is_active', 'is_verified'}
    for field, value in request.data.items():
        if field in allowed:
            setattr(user, field, value)
    user.save()
    return Response(AdminUserSerializer(user).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_projects_list(request):
    """Liste des projets avec filtre par statut."""
    status_filter = request.query_params.get('status', '').strip()

    qs = Project.objects.select_related('user').prefetch_related('ai_plans')
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = qs.order_by('-created_at')[:200]
    return Response(AdminProjectSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_ai_jobs(request):
    """Liste des jobs de génération IA avec filtre par statut."""
    status_filter = request.query_params.get('status', '').strip()

    qs = GenerationJob.objects.select_related('project', 'project__user')
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = qs.order_by('-created_at')[:100]
    return Response(AdminGenerationJobSerializer(qs, many=True).data)
