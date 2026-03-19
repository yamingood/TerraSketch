"""
Custom permissions for TerraSketch project.
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the object has a 'user' or 'owner' field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsProVerified(BasePermission):
    """
    Permission for verified professional users only.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role not in ['pro', 'agency']:
            return False
            
        # Check if the user has a verified professional profile
        if hasattr(request.user, 'pro_profile'):
            return request.user.pro_profile.is_verified
        return False


class IsProOrUnverified(BasePermission):
    """
    Permission for professional users (verified or not).
    Used for profile creation/editing endpoints.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['pro', 'agency']


class IsPolsiaAdmin(BasePermission):
    """
    Permission for Polsia admin users only.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'


class IsSubscribed(BasePermission):
    """
    Permission that checks if user has an active subscription.
    Can be parameterized with minimum plan level.
    """
    def __init__(self, min_plan=None):
        self.min_plan = min_plan
        
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has an active subscription
        subscription = getattr(request.user, 'subscription', None)
        if not subscription or subscription.status != 'active':
            return False
            
        # If minimum plan is specified, check plan hierarchy
        if self.min_plan:
            plan_hierarchy = {
                'discovery': 0,
                'particular': 1,
                'pro': 2,
                'agency': 3
            }
            user_plan_level = plan_hierarchy.get(subscription.plan, 0)
            required_level = plan_hierarchy.get(self.min_plan, 0)
            
            return user_plan_level >= required_level
            
        return True


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission to allow read access to any user,
    but write access only to the owner.
    """
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False