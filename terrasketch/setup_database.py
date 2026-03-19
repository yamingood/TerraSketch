#!/usr/bin/env python
"""
Script de configuration complète de la base de données TerraSketch
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def setup_database():
    """Configuration complète de la base de données"""
    print("🚀 Configuration de la base de données TerraSketch...")
    
    # Activer l'environnement virtuel
    venv_activate = "source venv/bin/activate"
    
    # 1. Migrations Django
    print("\n📋 Étape 1: Migrations Django")
    commands = [
        f"{venv_activate} && python manage.py makemigrations",
        f"{venv_activate} && python manage.py migrate"
    ]
    
    for cmd in commands:
        if not run_command(cmd, "Migration Django"):
            return False
    
    # 2. Créer un superutilisateur
    print("\n👤 Étape 2: Création du superutilisateur")
    if not run_command(f"{venv_activate} && python create_test_user.py", "Création du utilisateur de test"):
        return False
    
    # 3. Importer la base de données de plantes
    print("\n🌿 Étape 3: Importation de la base de données de plantes")
    if not run_command(f"{venv_activate} && python import_plants_database.py", "Importation des plantes"):
        return False
    
    print("\n🎉 Configuration de la base de données terminée avec succès!")
    print("\n📊 Résumé:")
    
    # Afficher les statistiques
    if run_command(f"{venv_activate} && python -c \"import django; django.setup(); from apps.plants.models import Plant, PlantFamily; print(f'  • {{Plant.objects.count()}} plantes'); print(f'  • {{PlantFamily.objects.count()}} familles')\"", "Calcul des statistiques"):
        pass
    
    print("\n🚀 Vous pouvez maintenant :")
    print("  1. Démarrer le serveur Django: python manage.py runserver")
    print("  2. Tester les APIs avec les données importées")
    print("  3. Configurer PostgreSQL pour la production")

if __name__ == '__main__':
    # Définir les variables d'environnement Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.migration_minimal')
    
    setup_database()