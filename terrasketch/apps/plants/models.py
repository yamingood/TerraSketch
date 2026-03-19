"""
Plant models for TerraSketch.
"""
import uuid
# from django.contrib.postgres.fields import ArrayField  # Comment out for SQLite compatibility
from django.db import models
from django.utils.translation import gettext_lazy as _


class PlantFamily(models.Model):
    """
    Plant family model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_fr = models.CharField(_('nom français'), max_length=100)
    name_latin = models.CharField(_('nom latin'), max_length=100)
    
    class Meta:
        verbose_name = _('famille de plante')
        verbose_name_plural = _('familles de plantes')
        
    def __str__(self):
        return f'{self.name_fr} ({self.name_latin})'


class Plant(models.Model):
    """
    Main plant model.
    """
    TYPE_CHOICES = [
        ('tree', _('Arbre')),
        ('shrub', _('Arbuste')),
        ('perennial', _('Vivace')),
        ('annual', _('Annuelle')),
        ('grass', _('Graminée')),
        ('groundcover', _('Couvre-sol')),
        ('climber', _('Grimpante')),
        ('aquatic', _('Aquatique')),
        ('bulb', _('Bulbeuse')),
    ]
    
    GROWTH_RATE_CHOICES = [
        ('slow', _('Lente')),
        ('moderate', _('Modérée')),
        ('fast', _('Rapide')),
    ]
    
    FOLIAGE_CHOICES = [
        ('deciduous', _('Caduc')),
        ('evergreen', _('Persistant')),
        ('semi_evergreen', _('Semi-persistant')),
    ]
    
    WATER_NEED_CHOICES = [
        ('low', _('Faible')),
        ('moderate', _('Modéré')),
        ('high', _('Élevé')),
    ]
    
    SUN_EXPOSURE_CHOICES = [
        ('full_sun', _('Plein soleil')),
        ('partial_shade', _('Mi-ombre')),
        ('full_shade', _('Ombre')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        PlantFamily,
        on_delete=models.CASCADE,
        verbose_name=_('famille'),
        related_name='plants'
    )
    name_common_fr = models.CharField(_('nom commun français'), max_length=200)
    name_latin = models.CharField(_('nom latin'), max_length=200)
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    
    # Size characteristics
    height_adult_min_cm = models.IntegerField(
        _('hauteur adulte min (cm)'),
        blank=True,
        null=True
    )
    height_adult_max_cm = models.IntegerField(
        _('hauteur adulte max (cm)'),
        blank=True,
        null=True
    )
    width_adult_min_cm = models.IntegerField(
        _('largeur adulte min (cm)'),
        blank=True,
        null=True
    )
    width_adult_max_cm = models.IntegerField(
        _('largeur adulte max (cm)'),
        blank=True,
        null=True
    )
    
    # Growth characteristics
    growth_rate = models.CharField(
        _('vitesse de croissance'),
        max_length=20,
        choices=GROWTH_RATE_CHOICES,
        blank=True
    )
    foliage = models.CharField(
        _('feuillage'),
        max_length=20,
        choices=FOLIAGE_CHOICES,
        blank=True
    )
    
    # Flowering
    flowering_months = models.JSONField(
        _('mois de floraison'),
        default=list,
        blank=True,
        help_text=_('Liste des mois de floraison (1-12)')
    )
    flowering_color = models.CharField(
        _('couleur floraison'),
        max_length=50,
        blank=True
    )
    
    # Climate and care
    is_drought_resistant = models.BooleanField(
        _('résistant à la sécheresse'),
        default=False
    )
    frost_resistance_min_c = models.IntegerField(
        _('résistance au gel min (°C)'),
        blank=True,
        null=True
    )
    water_need = models.CharField(
        _('besoin en eau'),
        max_length=20,
        choices=WATER_NEED_CHOICES,
        blank=True
    )
    sun_exposure = models.CharField(
        _('exposition solaire'),
        max_length=20,
        choices=SUN_EXPOSURE_CHOICES,
        blank=True
    )
    soil_preference = models.JSONField(
        _('préférence de sol'),
        default=dict,
        blank=True,
        help_text=_('Dictionnaire des préférences de sol')
    )
    
    # Ecological aspects
    is_invasive = models.BooleanField(
        _('invasif'),
        default=False
    )
    attracts_pollinators = models.BooleanField(
        _('attire les pollinisateurs'),
        default=False
    )
    climate_zones = models.JSONField(
        _('zones climatiques'),
        default=list,
        blank=True,
        help_text=_('Liste des zones climatiques compatibles')
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('plante')
        verbose_name_plural = _('plantes')
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['water_need']),
            models.Index(fields=['sun_exposure']),
        ]
        
    def __str__(self):
        return f'{self.name_common_fr} ({self.name_latin})'
    
    @property
    def height_range_display(self):
        """Return height range as string."""
        if self.height_adult_min_cm and self.height_adult_max_cm:
            return f'{self.height_adult_min_cm}-{self.height_adult_max_cm} cm'
        elif self.height_adult_max_cm:
            return f'jusqu\'à {self.height_adult_max_cm} cm'
        return 'Taille non spécifiée'


class PlantStyle(models.Model):
    """
    Plant style affinity model.
    """
    STYLE_CHOICES = [
        ('mediterranean', _('Méditerranéen')),
        ('japanese', _('Japonais')),
        ('tropical', _('Tropical')),
        ('contemporary', _('Contemporain')),
        ('countryside', _('Champêtre')),
    ]
    
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        verbose_name=_('plante'),
        related_name='style_affinities'
    )
    style = models.CharField(
        _('style'),
        max_length=20,
        choices=STYLE_CHOICES
    )
    affinity_score = models.IntegerField(
        _('score d\'affinité'),
        help_text=_('Score de 1 à 10')
    )
    
    class Meta:
        verbose_name = _('affinité de style')
        verbose_name_plural = _('affinités de style')
        unique_together = ['plant', 'style']
        
    def __str__(self):
        return f'{self.plant.name_common_fr} - {self.get_style_display()} ({self.affinity_score}/10)'


class PlantCompanion(models.Model):
    """
    Plant companion relationships.
    """
    RELATIONSHIP_CHOICES = [
        ('beneficial', _('Bénéfique')),
        ('neutral', _('Neutre')),
        ('incompatible', _('Incompatible')),
    ]
    
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        verbose_name=_('plante'),
        related_name='companions'
    )
    companion_plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        verbose_name=_('plante compagnon'),
        related_name='companion_of'
    )
    relationship = models.CharField(
        _('relation'),
        max_length=20,
        choices=RELATIONSHIP_CHOICES
    )
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('association de plantes')
        verbose_name_plural = _('associations de plantes')
        unique_together = ['plant', 'companion_plant']
        
    def __str__(self):
        return f'{self.plant.name_common_fr} + {self.companion_plant.name_common_fr}'


class Plant3DModel(models.Model):
    """
    3D models for plants at different growth stages.
    """
    GROWTH_STAGE_CHOICES = [
        ('young', _('Jeune')),
        ('intermediate', _('Intermédiaire')),
        ('adult', _('Adulte')),
    ]
    
    SOURCE_CHOICES = [
        ('speedtree', _('SpeedTree')),
        ('maxtree', _('Maxtree')),
        ('polyhaven', _('Poly Haven')),
        ('custom', _('Personnalisé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        verbose_name=_('plante'),
        related_name='models_3d'
    )
    growth_stage = models.CharField(
        _('stade de croissance'),
        max_length=20,
        choices=GROWTH_STAGE_CHOICES
    )
    model_url = models.URLField(
        _('URL du modèle'),
        help_text=_('URL du fichier GLTF/GLB sur R2')
    )
    thumbnail_url = models.URLField(
        _('URL miniature'),
        blank=True
    )
    height_in_model_cm = models.IntegerField(
        _('hauteur dans le modèle (cm)')
    )
    source = models.CharField(
        _('source'),
        max_length=20,
        choices=SOURCE_CHOICES,
        default='custom'
    )
    
    class Meta:
        verbose_name = _('modèle 3D de plante')
        verbose_name_plural = _('modèles 3D de plantes')
        unique_together = ['plant', 'growth_stage']
        
    def __str__(self):
        return f'{self.plant.name_common_fr} - {self.get_growth_stage_display()}'


class PlantCareTemplate(models.Model):
    """
    Care templates for plants by month and climate.
    """
    TASK_TYPE_CHOICES = [
        ('watering', _('Arrosage')),
        ('pruning', _('Taille')),
        ('fertilizing', _('Fertilisation')),
        ('mulching', _('Paillage')),
        ('protection', _('Protection')),
        ('inspection', _('Inspection')),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', _('Critique')),
        ('recommended', _('Recommandé')),
        ('optional', _('Optionnel')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        verbose_name=_('plante'),
        related_name='care_templates'
    )
    month = models.IntegerField(
        _('mois'),
        help_text=_('Mois de 1 à 12')
    )
    task_type = models.CharField(
        _('type de tâche'),
        max_length=20,
        choices=TASK_TYPE_CHOICES
    )
    description = models.TextField(_('description'))
    priority = models.CharField(
        _('priorité'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='recommended'
    )
    climate_zone = models.CharField(
        _('zone climatique'),
        max_length=50,
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('modèle d\'entretien')
        verbose_name_plural = _('modèles d\'entretien')
        
    def __str__(self):
        return f'{self.plant.name_common_fr} - {self.get_task_type_display()} (mois {self.month})'
