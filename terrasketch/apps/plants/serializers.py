from rest_framework import serializers
from .models import Plant, PlantFamily, PlantStyle, PlantCompanion, Plant3DModel, PlantCareTemplate

class PlantFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantFamily
        fields = '__all__'

class PlantStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantStyle
        fields = '__all__'

class PlantCompanionSerializer(serializers.ModelSerializer):
    companion_plant = serializers.StringRelatedField()
    
    class Meta:
        model = PlantCompanion
        fields = '__all__'

class Plant3DModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant3DModel
        fields = '__all__'

class PlantCareTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantCareTemplate
        fields = '__all__'

class PlantListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des plantes"""
    family = PlantFamilySerializer(read_only=True)
    style_affinities = PlantStyleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Plant
        fields = ('id', 'name_common_fr', 'name_latin', 'family', 'style_affinities', 'height_adult_max_cm',
                 'sun_exposure', 'water_need', 'frost_resistance_min_c')

class PlantDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour les détails d'une plante"""
    family = PlantFamilySerializer(read_only=True)
    style_affinities = PlantStyleSerializer(many=True, read_only=True)
    companions = PlantCompanionSerializer(many=True, read_only=True)
    models_3d = Plant3DModelSerializer(many=True, read_only=True)
    care_templates = PlantCareTemplateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Plant
        fields = '__all__'

class PlantSearchSerializer(serializers.Serializer):
    """Serializer pour les paramètres de recherche de plantes"""
    search = serializers.CharField(required=False, allow_blank=True)
    family = serializers.CharField(required=False, allow_blank=True)
    style = serializers.CharField(required=False, allow_blank=True)
    sun_requirements = serializers.ChoiceField(
        choices=[('full_sun', 'Plein soleil'), ('partial_shade', 'Mi-ombre'), ('full_shade', 'Ombre complète')],
        required=False
    )
    water_needs = serializers.ChoiceField(
        choices=[('low', 'Faible'), ('medium', 'Modéré'), ('high', 'Élevé')],
        required=False
    )
    hardiness_zone_min = serializers.IntegerField(required=False, min_value=1, max_value=11)
    hardiness_zone_max = serializers.IntegerField(required=False, min_value=1, max_value=11)
    height_min = serializers.FloatField(required=False, min_value=0)
    height_max = serializers.FloatField(required=False, min_value=0)
    price_min = serializers.FloatField(required=False, min_value=0)
    price_max = serializers.FloatField(required=False, min_value=0)