from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.admin_stats, name='admin-stats'),
    path('users/', views.admin_users_list, name='admin-users-list'),
    path('users/<uuid:user_id>/', views.admin_user_update, name='admin-user-update'),
    path('projects/', views.admin_projects_list, name='admin-projects-list'),
    path('ai-jobs/', views.admin_ai_jobs, name='admin-ai-jobs'),
]
