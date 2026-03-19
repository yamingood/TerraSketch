#!/usr/bin/env python
"""
Script de test pour l'API Anthropic Claude
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.ai.generator.claude_client import ClaudeClient
from django.conf import settings

def test_anthropic_connection():
    """Test de base de la connexion à l'API Anthropic"""
    
    # Vérifier la clé API
    api_key = settings.ANTHROPIC_API_KEY
    print(f"🔑 Clé API configurée: {'✅ Oui' if api_key and api_key != 'sk-ant-your-key-here' else '❌ Non'}")
    
    if not api_key or api_key == 'sk-ant-your-key-here':
        print("\n⚠️  ATTENTION: Clé API non configurée ou en placeholder")
        print("📝 Pour configurer la clé:")
        print("   1. Ouvre terrasketch/.env.local")
        print("   2. Remplace ANTHROPIC_API_KEY=sk-ant-your-key-here par ta vraie clé")
        print("   3. Relance ce script")
        return False
    
    # Test de connexion basique
    try:
        print("\n🧪 Test de connexion Claude...")
        client = ClaudeClient()
        
        # Test simple avec un prompt minimal
        test_prompt = "Réponds juste 'OK' pour confirmer que tu fonctionnes."
        
        print("📤 Envoi du prompt de test...")
        response = client.generate_response(test_prompt)
        
        print(f"📨 Réponse reçue: {response[:50]}...")
        print("✅ Connexion API Anthropic réussie !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            print("🔐 Problème d'authentification - vérifier la clé API")
        elif "rate" in str(e).lower() or "quota" in str(e).lower():
            print("📊 Quota/limite atteinte sur l'API")
        else:
            print("🔧 Autre erreur - vérifier la connectivité réseau")
            
        return False

if __name__ == "__main__":
    print("🚀 Test de connexion API Anthropic Claude\n" + "="*50)
    
    success = test_anthropic_connection()
    
    if success:
        print("\n🎉 API Anthropic prête pour l'intégration !")
        print("▶️  Prochaine étape: Créer l'endpoint upload cadastre")
    else:
        print("\n🛠️  Configurer la clé API avant de continuer")