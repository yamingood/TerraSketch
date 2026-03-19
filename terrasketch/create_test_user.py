#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.migration_minimal')
django.setup()

from apps.accounts.models import User, Subscription

# Créer un utilisateur testeur
print("Création de l'utilisateur testeur...")

# Supprimer l'utilisateur existant s'il existe
try:
    existing_user = User.objects.get(email='testeur@terrasketch.com')
    existing_user.delete()
    print("Utilisateur existant supprimé")
except User.DoesNotExist:
    pass

# Créer le nouvel utilisateur
user = User.objects.create_user(
    email='testeur@terrasketch.com',
    password='password123',
    first_name='Test',
    last_name='User',
    role='particular',
    is_verified=True
)

# Créer un abonnement pour l'utilisateur
subscription = Subscription.objects.create(
    user=user,
    plan='discovery',
    status='active'
)

print(f"✅ Utilisateur créé avec succès!")
print(f"📧 Email: testeur@terrasketch.com")
print(f"🔑 Mot de passe: password123")
print(f"👤 Rôle: {user.role}")
print(f"📋 Plan: {subscription.plan}")
print(f"🎯 Status: {subscription.status}")

print("\n🚀 Vous pouvez maintenant vous connecter avec ces identifiants!")