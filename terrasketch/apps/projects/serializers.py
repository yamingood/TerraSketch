from rest_framework import serializers
from .models import Project, Parcel, TerrainAnalysis, EarthworkRecommendation
from apps.accounts.serializers import UserSerializer

class ParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class TerrainAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerrainAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class EarthworkRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarthworkRecommendation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    parcels = ParcelSerializer(many=True, read_only=True)
    terrain_analyses = TerrainAnalysisSerializer(many=True, read_only=True)
    earthwork_recommendations = EarthworkRecommendationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'owner')

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)

class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des projets"""
    owner = serializers.StringRelatedField()
    parcels_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'project_type', 'status', 'budget_max',
                 'owner', 'created_at', 'updated_at', 'parcels_count', 'progress_percentage')
    
    def get_parcels_count(self, obj):
        return obj.parcels.count()
    
    def get_progress_percentage(self, obj):
        # Calcul simple du pourcentage de progression
        progress_indicators = [
            bool(obj.parcels.exists()),
            obj.status in ['design_in_progress', 'design_completed', 'completed'],
            obj.status in ['design_completed', 'completed'],
            obj.status == 'completed',
        ]
        return (sum(progress_indicators) / len(progress_indicators)) * 100