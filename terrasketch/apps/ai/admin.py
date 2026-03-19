from django.contrib import admin
from .models import Plan, GenerationJob, ClimateCache, PlantCompatibility, UserGenerationQuota


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'version', 'is_current', 'ai_model', 'input_tokens', 'output_tokens', 'generated_at')
    list_filter = ('is_current', 'ai_model', 'generated_at')
    search_fields = ('project__name', 'project__id')
    readonly_fields = ('generated_at',)
    ordering = ('-generated_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'progress_pct', 'current_step', 'created_at', 'started_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__name', 'project__id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')


@admin.register(ClimateCache)
class ClimateCacheAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'cached_at', 'is_expired')
    search_fields = ('latitude', 'longitude')
    readonly_fields = ('cached_at',)
    ordering = ('-cached_at',)
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expiré'


@admin.register(PlantCompatibility)
class PlantCompatibilityAdmin(admin.ModelAdmin):
    list_display = ('plant', 'zone_climatique', 'zone_rusticite', 'stress_hydrique', 'is_compatible', 'compatibility_score', 'calculated_at')
    list_filter = ('zone_climatique', 'zone_rusticite', 'stress_hydrique', 'is_compatible')
    search_fields = ('plant__name_latin', 'plant__name_common')
    readonly_fields = ('calculated_at',)
    ordering = ('-calculated_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('plant')


@admin.register(UserGenerationQuota)
class UserGenerationQuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'generations_count_today', 'generations_count_month', 'last_reset_date', 'last_generation_at', 'can_generate')
    list_filter = ('last_reset_date', 'last_generation_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_generation_at',)
    ordering = ('-last_generation_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def can_generate(self, obj):
        return obj.can_generate()
    can_generate.boolean = True
    can_generate.short_description = 'Peut générer'
