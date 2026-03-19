"""
Design models for TerraSketch - AI generation and 3D visualization.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Design(models.Model):
    """
    Design model for AI-generated landscape plans.
    """
    STYLE_CHOICES = [
        ('mediterranean', _('Méditerranéen')),
        ('japanese', _('Japonais')),
        ('tropical', _('Tropical')),
        ('contemporary', _('Contemporain')),
        ('countryside', _('Champêtre')),
    ]
    
    STATUS_CHOICES = [
        ('generating', _('Génération en cours')),
        ('draft', _('Brouillon')),
        ('validated', _('Validé')),
        ('error', _('Erreur')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('projet'),
        related_name='designs'
    )
    version = models.IntegerField(_('version'), default=1)
    style = models.CharField(
        _('style'),
        max_length=20,
        choices=STYLE_CHOICES
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='generating'
    )
    
    # Canvas dimensions
    canvas_width_m = models.FloatField(
        _('largeur canvas (m)'),
        blank=True,
        null=True
    )
    canvas_height_m = models.FloatField(
        _('hauteur canvas (m)'),
        blank=True,
        null=True
    )
    
    # Export URLs
    thumbnail_url = models.URLField(
        _('URL miniature'),
        blank=True
    )
    export_2d_url = models.URLField(
        _('URL export 2D'),
        blank=True
    )
    export_3d_url = models.URLField(
        _('URL export 3D'),
        blank=True
    )
    
    # AI Generation metadata
    generation_params = models.JSONField(
        _('paramètres de génération'),
        default=dict,
        blank=True,
        help_text=_('Paramètres envoyés à l\'IA')
    )
    ai_model_used = models.CharField(
        _('modèle IA utilisé'),
        max_length=50,
        blank=True
    )
    generated_at = models.DateTimeField(
        _('généré le'),
        blank=True,
        null=True
    )
    validated_at = models.DateTimeField(
        _('validé le'),
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('design')
        verbose_name_plural = _('designs')
        unique_together = ['project', 'version']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Design {self.project.name} v{self.version} ({self.get_style_display()})'
    
    @property
    def is_generating(self):
        """Return True if design is being generated."""
        return self.status == 'generating'
    
    @property
    def is_ready(self):
        """Return True if design is ready for use."""
        return self.status in ['draft', 'validated']


class DesignElement(models.Model):
    """
    Individual elements within a design (plants, paths, structures, etc.).
    """
    ELEMENT_TYPE_CHOICES = [
        ('plant', _('Plante')),
        ('path', _('Allée')),
        ('terrace', _('Terrasse')),
        ('wall', _('Mur')),
        ('water_feature', _('Point d\'eau')),
        ('furniture', _('Mobilier')),
        ('lighting', _('Éclairage')),
        ('fence', _('Clôture')),
        ('lawn', _('Pelouse')),
        ('mulch', _('Paillage')),
    ]
    
    ADDED_BY_CHOICES = [
        ('ai', _('IA')),
        ('user', _('Utilisateur')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        verbose_name=_('design'),
        related_name='elements'
    )
    plant = models.ForeignKey(
        'plants.Plant',
        on_delete=models.SET_NULL,
        verbose_name=_('plante'),
        blank=True,
        null=True,
        related_name='design_uses'
    )
    element_type = models.CharField(
        _('type d\'élément'),
        max_length=20,
        choices=ELEMENT_TYPE_CHOICES
    )
    label = models.CharField(
        _('libellé'),
        max_length=200,
        blank=True
    )
    
    # Geographic positioning (will be PostGIS in production)
    position = models.TextField(
        _('position'),
        help_text=_('Position centrale de l\'élément (GeoJSON Point)')
    )
    geometry = models.TextField(
        _('emprise au sol'),
        blank=True,
        null=True,
        help_text=_('Emprise géométrique de l\'élément (GeoJSON Polygon)')
    )
    rotation_deg = models.FloatField(
        _('rotation (degrés)'),
        default=0
    )
    
    # Quantity and spacing
    quantity = models.IntegerField(
        _('quantité'),
        default=1
    )
    spacing_cm = models.IntegerField(
        _('espacement (cm)'),
        blank=True,
        null=True
    )
    
    # Project phasing
    phase = models.IntegerField(
        _('phase'),
        default=1,
        help_text=_('Phase de réalisation (1, 2 ou 3)')
    )
    
    # Metadata
    is_locked = models.BooleanField(
        _('verrouillé'),
        default=False,
        help_text=_('Élément verrouillé contre modification')
    )
    notes = models.TextField(
        _('notes'),
        blank=True
    )
    added_by = models.CharField(
        _('ajouté par'),
        max_length=10,
        choices=ADDED_BY_CHOICES,
        default='ai'
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('élément de design')
        verbose_name_plural = _('éléments de design')
        indexes = [
            models.Index(fields=['design', 'element_type']),
            models.Index(fields=['design', 'phase']),
        ]
        
    def __str__(self):
        return f'{self.get_element_type_display()} - {self.label or self.plant}'
    
    @property
    def display_name(self):
        """Return display name for the element."""
        if self.plant:
            return self.plant.name_common_fr
        elif self.label:
            return self.label
        else:
            return self.get_element_type_display()


class TemporalSimulation(models.Model):
    """
    Temporal simulations showing design evolution over time.
    """
    HORIZON_CHOICES = [
        ('m3', _('3 mois')),
        ('m6', _('6 mois')),
        ('m12', _('12 mois')),
        ('m24', _('24 mois')),
    ]
    
    SEASON_CHOICES = [
        ('spring', _('Printemps')),
        ('summer', _('Été')),
        ('autumn', _('Automne')),
        ('winter', _('Hiver')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        verbose_name=_('design'),
        related_name='temporal_simulations'
    )
    horizon = models.CharField(
        _('horizon temporel'),
        max_length=10,
        choices=HORIZON_CHOICES
    )
    season = models.CharField(
        _('saison'),
        max_length=20,
        choices=SEASON_CHOICES
    )
    
    # Generated renders
    render_url = models.URLField(
        _('URL du rendu'),
        blank=True
    )
    video_url = models.URLField(
        _('URL de la vidéo'),
        blank=True,
        help_text=_('Plan Pro seulement')
    )
    
    # Alerts and conflicts
    density_alerts = models.JSONField(
        _('alertes de densité'),
        default=list,
        blank=True,
        help_text=_('Liste des conflits végétaux détectés')
    )
    
    generated_at = models.DateTimeField(_('généré le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('simulation temporelle')
        verbose_name_plural = _('simulations temporelles')
        unique_together = ['design', 'horizon', 'season']
        
    def __str__(self):
        return f'Simulation {self.design} - {self.get_horizon_display()} ({self.get_season_display()})'
    
    @property
    def has_conflicts(self):
        """Return True if simulation has density conflicts."""
        return len(self.density_alerts) > 0
