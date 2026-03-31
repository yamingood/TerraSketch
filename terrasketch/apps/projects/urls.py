from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Projets
    path('', views.ProjectListCreateView.as_view(), name='project_list_create'),
    path('<uuid:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('dashboard/stats/', views.project_dashboard_stats, name='dashboard_stats'),
    
    # Parcelles
    path('<uuid:project_id>/parcels/', views.ParcelListCreateView.as_view(), name='parcel_list_create'),
    path('<uuid:project_id>/parcels/<uuid:pk>/', views.ParcelDetailView.as_view(), name='parcel_detail'),
    
    # Analyse terrain
    path('<uuid:project_id>/analyze-terrain/', views.analyze_terrain, name='analyze_terrain'),
    
    # Génération IA
    path('<uuid:project_id>/generate/', views.generate_ai_plan, name='generate_ai_plan'),
    path('<uuid:project_id>/generate/<str:job_id>/', views.generation_status, name='generation_status'),

    # Plan courant
    path('<uuid:project_id>/plan/', views.project_current_plan, name='project_current_plan'),
]