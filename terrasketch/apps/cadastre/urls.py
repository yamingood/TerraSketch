"""
URLs pour le module cadastre.
"""
from django.urls import path
from .views import CadastreUploadView, CadastreStatusView

urlpatterns = [
    path("upload/", CadastreUploadView.as_view(), name="cadastre-upload"),
    path("status/", CadastreStatusView.as_view(), name="cadastre-status"),
]