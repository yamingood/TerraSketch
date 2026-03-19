"""
Budget and quote models for TerraSketch.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class BudgetPlan(models.Model):
    """
    Main budget plan for a project.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('projet'),
        related_name='budget_plan'
    )
    total_budget = models.DecimalField(
        _('budget total'),
        max_digits=10,
        decimal_places=2
    )
    
    # Budget breakdown by category
    budget_earthwork = models.DecimalField(
        _('budget terrassement'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    budget_plants = models.DecimalField(
        _('budget végétaux'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    budget_materials = models.DecimalField(
        _('budget matériaux'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    budget_labor = models.DecimalField(
        _('budget main d\'œuvre'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    budget_contingency_pct = models.FloatField(
        _('pourcentage d\'aléas'),
        default=10.0,
        help_text=_('Pourcentage de marge pour les imprévus')
    )
    
    currency = models.CharField(
        _('devise'),
        max_length=3,
        default='EUR'
    )
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('plan budgétaire')
        verbose_name_plural = _('plans budgétaires')
        
    def __str__(self):
        return f'Budget {self.project.name} - {self.total_budget}€'
    
    @property
    def budget_allocated(self):
        """Return sum of all allocated budgets."""
        return (self.budget_earthwork + self.budget_plants + 
                self.budget_materials + self.budget_labor)
    
    @property
    def budget_contingency(self):
        """Return contingency amount."""
        return self.budget_allocated * (self.budget_contingency_pct / 100)
    
    @property
    def budget_remaining(self):
        """Return remaining budget."""
        return self.total_budget - self.budget_allocated - self.budget_contingency
    
    @property
    def utilization_rate(self):
        """Return budget utilization rate as percentage."""
        if self.total_budget > 0:
            return (self.budget_allocated / self.total_budget) * 100
        return 0


class ProjectPhase(models.Model):
    """
    Project phases for phased implementation.
    """
    STATUS_CHOICES = [
        ('planned', _('Planifiée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('projet'),
        related_name='phases'
    )
    phase_number = models.IntegerField(
        _('numéro de phase'),
        help_text=_('1, 2 ou 3')
    )
    label = models.CharField(
        _('libellé'),
        max_length=200
    )
    planned_start_date = models.DateField(
        _('date de début prévue'),
        blank=True,
        null=True
    )
    planned_end_date = models.DateField(
        _('date de fin prévue'),
        blank=True,
        null=True
    )
    estimated_cost = models.DecimalField(
        _('coût estimé'),
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    
    class Meta:
        verbose_name = _('phase de projet')
        verbose_name_plural = _('phases de projet')
        unique_together = ['project', 'phase_number']
        ordering = ['phase_number']
        
    def __str__(self):
        return f'Phase {self.phase_number} - {self.label}'


class Quote(models.Model):
    """
    Quote/Devis model for projects.
    """
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('sent', _('Envoyé')),
        ('accepted', _('Accepté')),
        ('rejected', _('Refusé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name=_('projet'),
        related_name='quotes'
    )
    version = models.IntegerField(_('version'), default=1)
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    valid_until = models.DateField(
        _('valide jusqu\'au'),
        blank=True,
        null=True
    )
    
    # Pricing
    total_ht = models.DecimalField(
        _('total HT'),
        max_digits=10,
        decimal_places=2
    )
    tva_rate = models.FloatField(
        _('taux TVA'),
        default=20.0
    )
    total_ttc = models.DecimalField(
        _('total TTC'),
        max_digits=10,
        decimal_places=2
    )
    
    # Export and tracking
    pdf_url = models.URLField(
        _('URL PDF'),
        blank=True
    )
    sent_at = models.DateTimeField(
        _('envoyé le'),
        blank=True,
        null=True
    )
    accepted_at = models.DateTimeField(
        _('accepté le'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('devis')
        verbose_name_plural = _('devis')
        unique_together = ['project', 'version']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Devis {self.project.name} v{self.version}'
    
    def save(self, *args, **kwargs):
        # Auto-calculate TTC from HT
        self.total_ttc = self.total_ht * (1 + self.tva_rate / 100)
        super().save(*args, **kwargs)


class QuoteLineItem(models.Model):
    """
    Line items within a quote.
    """
    CATEGORY_CHOICES = [
        ('plant', _('Végétal')),
        ('material', _('Matériau')),
        ('earthwork', _('Terrassement')),
        ('labor', _('Main d\'œuvre')),
        ('other', _('Autre')),
    ]
    
    UNIT_CHOICES = [
        ('unit', _('Unité')),
        ('m2', _('m²')),
        ('m3', _('m³')),
        ('ml', _('ml')),
        ('forfait', _('Forfait')),
        ('jour', _('Jour')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        verbose_name=_('devis'),
        related_name='line_items'
    )
    design_element = models.ForeignKey(
        'designs.DesignElement',
        on_delete=models.SET_NULL,
        verbose_name=_('élément de design'),
        blank=True,
        null=True,
        related_name='quote_items'
    )
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    label = models.CharField(
        _('libellé'),
        max_length=200
    )
    description = models.TextField(
        _('description'),
        blank=True
    )
    unit = models.CharField(
        _('unité'),
        max_length=10,
        choices=UNIT_CHOICES
    )
    quantity = models.FloatField(_('quantité'))
    unit_price_ht = models.DecimalField(
        _('prix unitaire HT'),
        max_digits=10,
        decimal_places=2
    )
    total_ht = models.DecimalField(
        _('total HT'),
        max_digits=10,
        decimal_places=2
    )
    phase = models.IntegerField(
        _('phase'),
        default=1
    )
    
    class Meta:
        verbose_name = _('ligne de devis')
        verbose_name_plural = _('lignes de devis')
        
    def __str__(self):
        return f'{self.label} - {self.quantity} {self.unit}'
    
    def save(self, *args, **kwargs):
        # Auto-calculate total from quantity and unit price
        self.total_ht = Decimal(str(self.quantity)) * self.unit_price_ht
        super().save(*args, **kwargs)


class MarketPrice(models.Model):
    """
    Reference market prices for materials, plants, and labor.
    """
    CATEGORY_CHOICES = [
        ('plant', _('Végétal')),
        ('material', _('Matériau')),
        ('labor', _('Main d\'œuvre')),
        ('earthwork', _('Terrassement')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(
        _('catégorie'),
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    item_code = models.CharField(
        _('code article'),
        max_length=50
    )
    label = models.CharField(
        _('libellé'),
        max_length=200
    )
    unit = models.CharField(
        _('unité'),
        max_length=10
    )
    price_min = models.DecimalField(
        _('prix min'),
        max_digits=10,
        decimal_places=2
    )
    price_avg = models.DecimalField(
        _('prix moyen'),
        max_digits=10,
        decimal_places=2
    )
    price_max = models.DecimalField(
        _('prix max'),
        max_digits=10,
        decimal_places=2
    )
    region = models.CharField(
        _('région'),
        max_length=100,
        blank=True,
        null=True
    )
    valid_from = models.DateField(_('valide à partir du'))
    valid_until = models.DateField(_('valide jusqu\'au'))
    source = models.CharField(
        _('source'),
        max_length=200
    )
    
    class Meta:
        verbose_name = _('prix de référence')
        verbose_name_plural = _('prix de référence')
        indexes = [
            models.Index(fields=['category', 'item_code']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
        
    def __str__(self):
        return f'{self.label} - {self.price_avg}€/{self.unit}'
    
    @property
    def is_valid_now(self):
        """Check if price is currently valid."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.valid_from <= today <= self.valid_until
