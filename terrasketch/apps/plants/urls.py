from django.urls import path
from . import views

app_name = 'plants'

urlpatterns = [
    # Plantes
    path('', views.PlantListView.as_view(), name='plant_list'),
    path('<uuid:pk>/', views.PlantDetailView.as_view(), name='plant_detail'),
    path('families/', views.PlantFamilyListView.as_view(), name='plant_families'),
    path('styles/', views.PlantStyleListView.as_view(), name='plant_styles'),
    path('search-filters/', views.plant_search_filters, name='plant_search_filters'),
    
    # Recommandations
    path('recommendations/<uuid:project_id>/', views.plant_recommendations, name='plant_recommendations'),
]