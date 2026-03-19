"""
Models for IGN geographic enrichment
"""
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


class ParcelEnrichment(models.Model):
    """Données d'enrichissement IGN pour une parcelle cadastrale"""
    
    # Clés primaires
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel_id = models.CharField(max_length=50, unique=True, help_text="ID parcelle cadastrale")
    
    # Données altimétriques IGN
    elevation_min = models.FloatField(null=True, blank=True, help_text="Altitude min (m) - IGN RGE ALTI")
    elevation_max = models.FloatField(null=True, blank=True, help_text="Altitude max (m) - IGN RGE ALTI") 
    elevation_average = models.FloatField(null=True, blank=True, help_text="Altitude moyenne (m)")
    elevation_profile = models.JSONField(default=list, help_text="Profil altimétrique détaillé")
    slope_analysis = models.JSONField(default=dict, help_text="Analyse des pentes")
    
    # Occupation du sol OCS GE
    land_cover_data = models.JSONField(default=dict, help_text="OCS GE - occupation détaillée")
    vegetation_cover_pct = models.FloatField(null=True, blank=True, help_text="% couverture végétale")
    artificial_cover_pct = models.FloatField(null=True, blank=True, help_text="% surfaces artificialisées")
    water_cover_pct = models.FloatField(null=True, blank=True, help_text="% surfaces en eau")
    agricultural_cover_pct = models.FloatField(null=True, blank=True, help_text="% surfaces agricoles")
    
    # Données administratives
    address_normalized = models.CharField(max_length=255, null=True, blank=True, help_text="Adresse IGN normalisée")
    insee_code = models.CharField(max_length=5, null=True, blank=True, help_text="Code INSEE commune")
    department = models.CharField(max_length=3, null=True, blank=True, help_text="Département")
    region = models.CharField(max_length=2, null=True, blank=True, help_text="Région")
    quality_score = models.FloatField(null=True, blank=True, help_text="Score qualité géocodage (0-1)")
    
    # Contexte géographique
    distance_to_water = models.FloatField(null=True, blank=True, help_text="Distance cours d'eau (m)")
    distance_to_road = models.FloatField(null=True, blank=True, help_text="Distance route principale (m)")
    urban_density = models.CharField(max_length=20, null=True, blank=True, 
                                   choices=[
                                       ('sparse', 'Faible'),
                                       ('moderate', 'Modérée'),
                                       ('dense', 'Dense'),
                                       ('very_dense', 'Très dense')
                                   ],
                                   help_text="Densité urbaine")
    climate_zone_ign = models.CharField(max_length=50, null=True, blank=True, help_text="Zone climatique IGN")
    
    # Métadonnées enrichissement
    enriched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ign_data_version = models.CharField(max_length=20, default="2024.1", help_text="Version données IGN")
    cache_expires_at = models.DateTimeField(help_text="Expiration cache IGN (24h)")
    
    # Statut enrichissement
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'Traitement en cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
        ('expired', 'Expiré')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True, help_text="Message d'erreur si échec")
    retry_count = models.IntegerField(default=0, help_text="Nombre de tentatives")
    
    class Meta:
        verbose_name = "Enrichissement parcelle"
        verbose_name_plural = "Enrichissements parcelles"
        indexes = [
            models.Index(fields=['parcel_id']),
            models.Index(fields=['status']),
            models.Index(fields=['cache_expires_at']),
        ]
    
    def __str__(self):
        return f"IGN Enrichment {self.parcel_id} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Auto-set cache expiration to 24h from now"""
        if not self.cache_expires_at:
            self.cache_expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if IGN data cache is expired"""
        return timezone.now() > self.cache_expires_at
    
    @property
    def elevation_range(self):
        """Calculate elevation range"""
        if self.elevation_min is not None and self.elevation_max is not None:
            return self.elevation_max - self.elevation_min
        return None
    
    def mark_as_failed(self, error_message):
        """Mark enrichment as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()
    
    def mark_as_completed(self):
        """Mark enrichment as completed"""
        self.status = 'completed'
        self.error_message = None
        self.save()


class IGNUsageLog(models.Model):
    """Suivi des appels API IGN pour monitoring quota"""
    
    endpoint = models.CharField(max_length=100, help_text="Endpoint IGN appelé")
    parcel_id = models.CharField(max_length=50, null=True, blank=True)
    response_status = models.IntegerField(help_text="Code de réponse HTTP")
    response_time_ms = models.IntegerField(help_text="Temps de réponse en ms")
    success = models.BooleanField(help_text="Succès de l'appel")
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log utilisation IGN"
        verbose_name_plural = "Logs utilisation IGN"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.endpoint} - {self.response_status} ({self.response_time_ms}ms)"