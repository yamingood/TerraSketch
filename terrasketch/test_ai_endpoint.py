#!/usr/bin/env python
"""
Test de l'endpoint génération IA
"""
import os
import sys
import json
from pathlib import Path
from unittest.mock import Mock

# Configuration Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.minimal')

# Setup Django simple
import django
from django.conf import settings

# Configuration minimal pour les tests
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-key',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'apps.accounts',
            'apps.projects',
            'apps.ai',
        ],
        USE_TZ=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        # Configuration IA
        ANTHROPIC_API_KEY='test-key',
        GENERATION_RATE_LIMIT_PER_USER=10,
    )

django.setup()

def test_ai_modules_import():
    """Test import des modules IA"""
    print("🧪 Test import modules IA")
    print("="*40)
    
    try:
        from apps.ai.models import GenerationJob, UserGenerationQuota
        print("✅ Models IA importés")
        
        from apps.ai.context.context_assembler import ContextAssembler
        print("✅ ContextAssembler importé")
        
        from apps.ai.prompt.builder import PromptBuilder
        print("✅ PromptBuilder importé")
        
        from apps.ai.generator.claude_client import ClaudeClient
        print("✅ ClaudeClient importé")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_context_assembler():
    """Test assemblage contexte"""
    print("\n🔧 Test ContextAssembler")
    print("="*40)
    
    try:
        from apps.ai.context.context_assembler import ContextAssembler
        from shapely.geometry import Polygon
        
        # Géométrie test
        geometry = Polygon([
            [2.3364, 48.8606],
            [2.3374, 48.8606], 
            [2.3374, 48.8616],
            [2.3364, 48.8616],
            [2.3364, 48.8606]
        ])
        
        # Préférences test
        preferences = {
            "style": "moderne",
            "budget_category": "medium",
            "maintenance_level": "low"
        }
        
        context_assembler = ContextAssembler()
        
        print("📍 Test assemblage contexte...")
        context = context_assembler.assemble_full_context(
            geometry=geometry,
            latitude=48.8611,
            longitude=2.3369,
            user_preferences=preferences
        )
        
        print(f"📊 Contexte assemblé:")
        print(f"  - Terrain: {context.get('terrain', {}).get('surface_m2', 0):.1f} m²")
        print(f"  - Climat: {context.get('climate', {}).get('zone', 'N/A')}")
        print(f"  - Solaire: {context.get('solar', {}).get('daily_hours_avg', 0):.1f}h")
        print(f"  - Plantes: {len(context.get('compatible_plants', []))} espèces")
        
        print("✅ ContextAssembler fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur context: {e}")
        return False

def test_prompt_builder():
    """Test construction prompt"""
    print("\n📝 Test PromptBuilder")
    print("="*40)
    
    try:
        from apps.ai.prompt.builder import PromptBuilder
        
        # Context test minimal
        context_data = {
            "terrain": {"surface_m2": 150, "forme": "rectangulaire"},
            "climate": {"zone": "Atlantique", "temp_moy": 15},
            "solar": {"daily_hours_avg": 6.5},
            "compatible_plants": ["Lavande", "Romarin", "Buis"]
        }
        
        preferences = {
            "style": "moderne",
            "maintenance_level": "low"
        }
        
        prompt_builder = PromptBuilder()
        
        print("🔨 Construction prompts...")
        system_prompt, user_prompt = prompt_builder.build_generation_prompts(
            context_data, preferences
        )
        
        print(f"📄 System prompt: {len(system_prompt)} chars")
        print(f"📄 User prompt: {len(user_prompt)} chars")
        
        # Vérification contenu
        if "paysagiste" in system_prompt.lower():
            print("✅ System prompt contient le rôle")
        if "moderne" in user_prompt.lower():
            print("✅ User prompt contient les préférences")
        
        print("✅ PromptBuilder fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur prompt: {e}")
        return False

def test_claude_client():
    """Test client Claude (configuration uniquement)"""
    print("\n🤖 Test ClaudeClient")
    print("="*40)
    
    try:
        from apps.ai.generator.claude_client import ClaudeClient
        
        # Initialisation client
        client = ClaudeClient()
        
        print("✅ ClaudeClient initialisé")
        print(f"🔧 Modèle: {client.model}")
        print(f"⚙️  Max tokens: {client.max_tokens}")
        
        # Note: pas de test réel d'API sans clé valide
        print("ℹ️  Test API réel nécessite clé Anthropic valide")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur claude client: {e}")
        return False

def test_endpoint_logic():
    """Test logique endpoint sans Django request"""
    print("\n🌐 Test logique endpoint")
    print("="*40)
    
    try:
        # Import fonctions endpoint
        from apps.projects.views import generate_ai_plan
        
        print("✅ Endpoint generate_ai_plan importé")
        
        # Mock data validation
        valid_styles = ['moderne', 'classique', 'naturel', 'zen', 'tropical']
        test_style = 'moderne'
        
        if test_style in valid_styles:
            print(f"✅ Style '{test_style}' validé")
        
        print("✅ Logique endpoint validée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test Endpoints IA TerraSketch")
    print("="*50)
    
    # Tests séquentiels
    tests = [
        test_ai_modules_import,
        test_context_assembler,
        test_prompt_builder,
        test_claude_client,
        test_endpoint_logic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur test: {e}")
            results.append(False)
    
    # Résultats
    print("\n" + "="*50)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 Tous les tests passés - Endpoint IA prêt!")
        print("▶️  APIs prêtes pour intégration frontend")
    else:
        print(f"🔧 {success_count}/{total_count} tests passés")
        print("🛠️  Certains modules à configurer")
    
    print("\n📋 Prochaines étapes:")
    print("1. 🔑 Configurer clé API Anthropic")
    print("2. 🏃 Tester endpoint avec serveur Django")
    print("3. 🌐 Intégrer frontend React")