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
]