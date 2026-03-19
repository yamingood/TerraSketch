"""
User and subscription models for TerraSketch.
"""
import uuid
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """Manager pour le modèle User personnalisé utilisant email au lieu de username."""
    
    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for TerraSketch.
    """
    ROLE_CHOICES = [
        ('particular', _('Particulier')),
        ('pro', _('Professionnel')),
        ('agency', _('Agence')),
        ('admin', _('Administrateur Polsia')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('adresse email'), unique=True)
    first_name = models.CharField(_('prénom'), max_length=30, blank=True)
    last_name = models.CharField(_('nom'), max_length=150, blank=True)
    role = models.CharField(
        _('rôle'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='particular'
    )
    stripe_customer_id = models.CharField(
        _('ID client Stripe'),
        max_length=255,
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        _('email vérifié'),
        default=False,
        help_text=_('Indique si l\'email de l\'utilisateur a été vérifié.')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    username = None  # Remove username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name for the user."""
        return f'{self.first_name} {self.last_name}'.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name


class Subscription(models.Model):
    """
    User subscription model.
    """
    PLAN_CHOICES = [
        ('discovery', _('Discovery')),
        ('particular', _('Particulier')),
        ('pro', _('Pro')),
        ('agency', _('Agence')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('cancelled', _('Annulé')),
        ('past_due', _('En retard')),
        ('trialing', _('Essai')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('utilisateur'),
        related_name='subscription'
    )
    plan = models.CharField(
        _('plan'),
        max_length=20,
        choices=PLAN_CHOICES,
        default='discovery'
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='trialing'
    )
    stripe_subscription_id = models.CharField(
        _('ID abonnement Stripe'),
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )
    current_period_start = models.DateTimeField(
        _('début période actuelle'),
        blank=True,
        null=True
    )
    current_period_end = models.DateTimeField(
        _('fin période actuelle'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('abonnement')
        verbose_name_plural = _('abonnements')
        
    def __str__(self):
        return f'{self.user.email} - {self.plan} ({self.status})'
    
    @property
    def is_active(self):
        """Return True if subscription is active."""
        return self.status == 'active'


class Organization(models.Model):
    """
    Organization model for agency users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('nom'), max_length=255)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('propriétaire'),
        related_name='owned_organizations'
    )
    logo_url = models.URLField(_('logo URL'), blank=True, null=True)
    white_label_domain = models.CharField(
        _('domaine marque blanche'),
        max_length=255,
        blank=True,
        null=True
    )
    siren = models.CharField(
        _('numéro SIREN'),
        max_length=20,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('organisation')
        verbose_name_plural = _('organisations')
        
    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """
    Membership model for organizations.
    """
    ROLE_CHOICES = [
        ('admin', _('Administrateur')),
        ('member', _('Membre')),
        ('viewer', _('Observateur')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name=_('organisation'),
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('utilisateur'),
        related_name='organization_memberships'
    )
    role = models.CharField(
        _('rôle'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(_('rejoint le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('membre d\'organisation')
        verbose_name_plural = _('membres d\'organisation')
        unique_together = ['organization', 'user']
        
    def __str__(self):
        return f'{self.user.email} - {self.organization.name} ({self.role})'