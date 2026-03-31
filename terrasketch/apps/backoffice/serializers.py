from rest_framework import serializers
from apps.accounts.models import User, Subscription
from apps.projects.models import Project
from apps.ai.models import GenerationJob


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    subscription_plan = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_verified', 'is_active', 'created_at',
            'subscription_plan', 'subscription_status', 'projects_count',
        )

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email

    def get_subscription_plan(self, obj):
        try:
            return obj.subscription.plan
        except Subscription.DoesNotExist:
            return None

    def get_subscription_status(self, obj):
        try:
            return obj.subscription.status
        except Subscription.DoesNotExist:
            return None

    def get_projects_count(self, obj):
        return obj.projects.count()


class AdminProjectSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    ai_plans_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'status', 'user_email', 'city',
            'budget_tier', 'created_at', 'updated_at', 'ai_plans_count',
        )

    def get_user_email(self, obj):
        return obj.user.email

    def get_ai_plans_count(self, obj):
        return obj.ai_plans.count()


class AdminGenerationJobSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = GenerationJob
        fields = (
            'id', 'status', 'progress_pct', 'current_step', 'error_message',
            'started_at', 'completed_at', 'created_at',
            'project_name', 'user_email',
        )

    def get_project_name(self, obj):
        return obj.project.name

    def get_user_email(self, obj):
        return obj.project.user.email
