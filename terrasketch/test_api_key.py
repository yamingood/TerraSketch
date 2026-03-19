#!/usr/bin/env python
"""
Test basique de la clé API Anthropic
"""
import anthropic
from pathlib import Path

def test_api_key():
    """Test de base pour vérifier la clé API"""
    
    # Lire clé API
    env_file = Path(__file__).parent / '.env.local'
    api_key = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    print("🔑 Test validité clé API Anthropic")
    print("="*40)
    
    if not api_key:
        print("❌ Pas de clé API trouvée")
        return False
    
    print(f"🔧 Clé trouvée: {api_key[:20]}...")
    
    try:
        # Initialisation client basique
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test avec une requête simple
        print("📡 Test connexion...")
        
        response = client.messages.create(
            model="claude-sonnet-4-6",  # Nouveau modèle suggéré
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        print("✅ Connexion réussie!")
        return True
        
    except anthropic.AuthenticationError as e:
        print(f"❌ Erreur authentification: {e}")
        print("🔧 Vérifier que la clé API est valide et active")
        return False
    except anthropic.NotFoundError as e:
        print(f"❌ Modèle non trouvé: {e}")
        print("🔧 Le modèle spécifié n'existe pas")
        return False
    except anthropic.RateLimitError as e:
        print(f"⚠️ Rate limit: {e}")
        print("🔧 Trop de requêtes, attendre")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    
    if success:
        print("\n🎉 Clé API Anthropic validée!")
    else:
        print("\n🛠️ Problème avec la clé API")
        print("📋 Actions:")
        print("1. Vérifier clé sur https://console.anthropic.com/")
        print("2. S'assurer que le compte a des crédits")
        print("3. Vérifier que l'API est activée")