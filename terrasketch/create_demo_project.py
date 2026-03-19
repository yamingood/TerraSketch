#!/usr/bin/env python
"""
Script pour créer un projet de démonstration
"""
import os
import sys
import uuid
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.migration_minimal')
django.setup()

from django.contrib.auth import get_user_model
from apps.projects.models import Project

User = get_user_model()

def create_demo_project():
    """Créer un projet de démonstration"""
    # Récupérer ou créer l'utilisateur testeur
    user, created = User.objects.get_or_create(
        email='testeur@terrasketch.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'particular',
            'is_verified': True
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ Utilisateur testeur créé: {user.email}")
    
    # Créer le projet de démonstration avec un UUID spécifique
    demo_uuid = uuid.UUID('12345678-1234-5678-9abc-123456789abc')
    
    try:
        demo_project = Project.objects.get(id=demo_uuid)
        created = False
    except Project.DoesNotExist:
        demo_project = Project.objects.create(
            id=demo_uuid,
            user=user,
            name='Jardin Méditerranéen - Villa Nice',
            status='draft',
            address='123 Avenue des Fleurs',
            city='Nice',
            postal_code='06000',
            budget_tier='structured',
            phase_plan=True
        )
        created = True
    
    if created:
        print(f"✅ Projet de démonstration créé: {demo_project.name}")
    else:
        print(f"ℹ️  Projet de démonstration existant: {demo_project.name}")
    
    return demo_project

if __name__ == '__main__':
    try:
        project = create_demo_project()
        print(f"\n🎉 Projet créé avec l'ID: {project.id}")
        print("Vous pouvez maintenant tester les recommandations IA!")
    except Exception as e:
        print(f"❌ Erreur: {e}")