from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()


class Plan(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='ai_plans')
    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True)
    
    # Données du plan
    plan_json = models.JSONField()  # Réponse complète Claude
    context_snapshot = models.JSONField(null=True, blank=True)  # Contexte utilisé pour générer
    prompt_snapshot = models.TextField(null=True, blank=True)  # Prompt exact envoyé
    budget_json = models.JSONField(null=True, blank=True)  # Résultat resolve_plan_budget()
    
    # Métadonnées génération
    ai_model = models.CharField(max_length=50, null=True, blank=True)
    input_tokens = models.IntegerField(null=True, blank=True)
    output_tokens = models.IntegerField(null=True, blank=True)
    generation_time_s = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        indexes = [
            models.Index(fields=['project', 'is_current']),
        ]
        unique_together = [
            ['project', 'version']
        ]
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other plans for this project as non-current
            Plan.objects.filter(project=self.project, is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Plan v{self.version} - {self.project.name}"


class GenerationJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True)  # job_id
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='generation_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_pct = models.IntegerField(default=0)
    current_step = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate unique ID with job_ prefix
            self.id = f"job_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Job de génération"
        verbose_name_plural = "Jobs de génération"
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Job {self.id} - {self.status}"


class ClimateCache(models.Model):
    """Cache pour les données climatiques Open-Meteo"""
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    data = models.JSONField()  # Données météo complètes
    cached_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['latitude', 'longitude']
        ]
        verbose_name = "Cache climatique"
        verbose_name_plural = "Caches climatiques"
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['cached_at']),
        ]
    
    def __str__(self):
        return f"Climat {self.latitude}, {self.longitude}"
    
    @property
    def is_expired(self):
        """Cache expire après 24h"""
        from datetime import timedelta
        from django.utils import timezone
        return timezone.now() - self.cached_at > timedelta(hours=24)


class PlantCompatibility(models.Model):
    """Cache des compatibilités plantes calculées"""
    plant = models.ForeignKey('plants.Plant', on_delete=models.CASCADE)
    zone_climatique = models.CharField(max_length=20)  # Atlantique, Continental, etc.
    zone_rusticite = models.CharField(max_length=10)   # Z8a, Z8b, etc.
    stress_hydrique = models.CharField(max_length=20)  # faible, modere, fort
    is_compatible = models.BooleanField()
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Score 0-100
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['plant', 'zone_climatique', 'zone_rusticite', 'stress_hydrique']
        ]
        verbose_name = "Compatibilité plante"
        verbose_name_plural = "Compatibilités plantes"
        indexes = [
            models.Index(fields=['zone_climatique', 'zone_rusticite', 'is_compatible']),
            models.Index(fields=['plant', 'is_compatible']),
        ]
    
    def __str__(self):
        return f"{self.plant.name_latin} - {self.zone_climatique} ({self.is_compatible})"


class UserGenerationQuota(models.Model):
    """Suivi des quotas de génération par utilisateur"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='generation_quota')
    generations_count_today = models.IntegerField(default=0)
    generations_count_month = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    last_generation_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Quota de génération"
        verbose_name_plural = "Quotas de génération"
    
    def reset_daily_quota(self):
        """Reset le compteur quotidien"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.generations_count_today = 0
            self.last_reset_date = today
            self.save()
    
    def can_generate(self):
        """Vérifie si l'utilisateur peut générer un plan"""
        self.reset_daily_quota()
        # Limites par défaut (à adapter selon le plan)
        daily_limit = 5
        monthly_limit = 50
        return (
            self.generations_count_today < daily_limit and
            self.generations_count_month < monthly_limit
        )
    
    def increment_usage(self):
        """Incrémente les compteurs après une génération"""
        from django.utils import timezone
        self.reset_daily_quota()
        self.generations_count_today += 1
        self.generations_count_month += 1
        self.last_generation_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Quota {self.user.username} - {self.generations_count_today}/j, {self.generations_count_month}/m"