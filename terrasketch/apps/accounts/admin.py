"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Subscription, Organization, OrganizationMember


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
        (_('Stripe'), {'fields': ('stripe_customer_id',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Subscription admin."""
    list_display = ('user', 'plan', 'status', 'current_period_start', 'current_period_end', 'created_at')
    list_filter = ('plan', 'status', 'created_at')
    search_fields = ('user__email', 'stripe_subscription_id')
    readonly_fields = ('created_at',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization admin."""
    list_display = ('name', 'owner', 'siren', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__email', 'siren')
    readonly_fields = ('created_at',)


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Organization member admin."""
    list_display = ('user', 'organization', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'organization__name')
