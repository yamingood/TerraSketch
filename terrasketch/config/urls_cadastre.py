"""
URLs temporaires juste pour tester le module cadastre
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_view(request):
    return JsonResponse({
        'message': 'TerraSketch Cadastre API Test',
        'endpoints': {
            'status': '/api/cadastre/status/',
            'upload': '/api/cadastre/upload/'
        }
    })

urlpatterns = [
    path('api/cadastre/', include('apps.cadastre.urls')),
    path('', root_view),
]