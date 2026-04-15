"""
Project, Parcel and Terrain models for TerraSketch.
"""
import uuid
from django.db import models
# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point, Polygon
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    """
    Main project model.
    """
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('archived', _('Archivé')),
    ]
    
    BUDGET_TIER_CHOICES = [
        ('essential', _('Essentiel')),
        ('structured', _('Structuré')),
        ('premium', _('Premium')),
        ('prestige', _('Prestige')),
    ]

    GARDEN_STYLE_CHOICES = [
        ('contemporary', _('Contemporain')),
        ('mediterranean', _('Méditerranéen')),
        ('cottage', _('Cottage Anglais')),
        ('japanese', _('Japonais')),
        ('tropical', _('Tropical')),
        ('naturel', _('Naturel')),
    ]

    MAINTENANCE_LEVEL_CHOICES = [
        ('low', _('Faible — 1-2h/mois')),
        ('medium', _('Modéré — 3-5h/mois')),
        ('high', _('Intensif — 6h+/mois')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        verbose_name=_('utilisateur'),
        related_name='projects'
    )
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.SET_NULL,
        verbose_name=_('organisation'),
        related_name='projects',
        blank=True,
        null=True
    )
    name = models.CharField(_('nom'), max_length=255)
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    budget_total = models.DecimalField(
        _('budget total'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    budget_tier = models.CharField(
        _('gamme budget'),
        max_length=20,
        choices=BUDGET_TIER_CHOICES,
        blank=True,
        null=True
    )
    garden_style = models.CharField(
        _('style de jardin'),
        max_length=20,
        choices=GARDEN_STYLE_CHOICES,
        blank=True,
        null=True
    )
    maintenance_level = models.CharField(
        _('niveau d\'entretien'),
        max_length=10,
        choices=MAINTENANCE_LEVEL_CHOICES,
        blank=True,
        null=True
    )
    phase_plan = models.BooleanField(
        _('plan par phases'),
        default=False,
        help_text=_('Si le projet doit être réalisé en plusieurs phases')
    )
    address = models.CharField(_('adresse'), max_length=500, blank=True)
    city = models.CharField(_('ville'), max_length=100, blank=True)
    postal_code = models.CharField(_('code postal'), max_length=10, blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('projet')
        verbose_name_plural = _('projets')
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.name} - {self.user.get_full_name()}'


class Parcel(models.Model):
    """
    Land parcel model with geographic data.
    """
    SOURCE_CHOICES = [
        ('upload', _('Upload manuel')),
        ('ign_api', _('API IGN')),
        ('manual', _('Saisie manuelle')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('projet'),
        related_name='parcel'
    )
    cadastral_reference = models.CharField(
        _('référence cadastrale'),
        max_length=50,
        blank=True
    )
    geometry = models.TextField(
        _('géométrie'),
        blank=True,
        null=True,
        help_text=_('Contour de la parcelle en format GeoJSON (sera PostGIS en production)')
    )
    area_sqm = models.FloatField(
        _('surface (m²)'),
        blank=True,
        null=True
    )
    perimeter_m = models.FloatField(
        _('périmètre (m)'),
        blank=True,
        null=True
    )
    orientation = models.CharField(
        _('orientation'),
        max_length=50,
        blank=True,
        help_text=_('Ex: Sud-Ouest')
    )
    raw_file_url = models.URLField(
        _('fichier source'),
        blank=True,
        help_text=_('URL du fichier PDF/DXF uploadé sur R2')
    )
    source = models.CharField(
        _('source'),
        max_length=20,
        choices=SOURCE_CHOICES,
        default='upload'
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('parcelle')
        verbose_name_plural = _('parcelles')
        
    def __str__(self):
        return f'Parcelle {self.cadastral_reference} - {self.project.name}'
    
    def save(self, *args, **kwargs):
        # Calculate area and perimeter if geometry is provided
        if self.geometry:
            self.area_sqm = self.geometry.area * 111000 * 111000  # Approximate conversion from degrees to m²
            self.perimeter_m = self.geometry.length * 111000  # Approximate conversion from degrees to m
        super().save(*args, **kwargs)


class TerrainAnalysis(models.Model):
    """
    Terrain analysis data for a parcel.
    """
    SLOPE_CHOICES = [
        ('flat', _('Plat (0-2%)')),
        ('gentle', _('Pente douce (2-5%)')),
        ('moderate', _('Pente modérée (5-10%)')),
        ('steep', _('Pente forte (>10%)')),
    ]
    
    SOIL_TYPE_CHOICES = [
        ('clay', _('Argileux')),
        ('sandy', _('Sableux')),
        ('loamy', _('Limoneux')),
        ('chalky', _('Calcaire')),
        ('unknown', _('Inconnu')),
    ]
    
    DRAINAGE_RISK_CHOICES = [
        ('low', _('Faible')),
        ('medium', _('Moyen')),
        ('high', _('Élevé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel = models.OneToOneField(
        Parcel,
        on_delete=models.CASCADE,
        verbose_name=_('parcelle'),
        related_name='terrain_analysis'
    )
    slope_percent_avg = models.FloatField(
        _('pente moyenne (%)'),
        blank=True,
        null=True
    )
    slope_percent_max = models.FloatField(
        _('pente maximale (%)'),
        blank=True,
        null=True
    )
    slope_classification = models.CharField(
        _('classification pente'),
        max_length=20,
        choices=SLOPE_CHOICES,
        blank=True
    )
    has_water_accumulation = models.BooleanField(
        _('accumulation d\'eau'),
        default=False
    )
    soil_type = models.CharField(
        _('type de sol'),
        max_length=20,
        choices=SOIL_TYPE_CHOICES,
        default='unknown'
    )
    soil_ph = models.FloatField(
        _('pH du sol'),
        blank=True,
        null=True
    )
    drainage_risk = models.CharField(
        _('risque de drainage'),
        max_length=20,
        choices=DRAINAGE_RISK_CHOICES,
        default='medium'
    )
    mnt_file_url = models.URLField(
        _('fichier MNT'),
        blank=True,
        help_text=_('URL du fichier Modèle Numérique de Terrain')
    )
    ign_data_used = models.BooleanField(
        _('données IGN utilisées'),
        default=False
    )
    analyzed_at = models.DateTimeField(_('analysé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('analyse terrain')
        verbose_name_plural = _('analyses terrain')
        
    def __str__(self):
        return f'Analyse {self.parcel.project.name}'


class EarthworkRecommendation(models.Model):
    """
    Earthwork recommendations based on terrain analysis.
    """
    TYPE_CHOICES = [
        ('leveling', _('Nivellement')),
        ('slope_planting', _('Plantation sur pente')),
        ('retaining_wall', _('Mur de soutènement')),
        ('peripheral_drainage', _('Drainage périphérique')),
        ('backfill', _('Remblai')),
        ('excavation', _('Déblai')),
    ]
    
    PRIORITY_CHOICES = [
        ('required', _('Obligatoire')),
        ('recommended', _('Recommandé')),
        ('optional', _('Optionnel')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    terrain_analysis = models.ForeignKey(
        TerrainAnalysis,
        on_delete=models.CASCADE,
        verbose_name=_('analyse terrain'),
        related_name='earthwork_recommendations'
    )
    type = models.CharField(
        _('type'),
        max_length=30,
        choices=TYPE_CHOICES
    )
    zone_geometry = models.TextField(
        _('zone géométrique'),
        blank=True,
        null=True,
        help_text=_('Zone concernée par la recommandation (GeoJSON)')
    )
    area_sqm = models.FloatField(
        _('surface (m²)'),
        blank=True,
        null=True
    )
    volume_m3 = models.FloatField(
        _('volume (m³)'),
        blank=True,
        null=True
    )
    estimated_cost_min = models.DecimalField(
        _('coût estimé min'),
        max_digits=10,
        decimal_places=2
    )
    estimated_cost_max = models.DecimalField(
        _('coût estimé max'),
        max_digits=10,
        decimal_places=2
    )
    priority = models.CharField(
        _('priorité'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='recommended'
    )
    description = models.TextField(_('description'))
    
    class Meta:
        verbose_name = _('recommandation terrassement')
        verbose_name_plural = _('recommandations terrassement')
        
    def __str__(self):
        return f'{self.get_type_display()} - {self.terrain_analysis.parcel.project.name}'
