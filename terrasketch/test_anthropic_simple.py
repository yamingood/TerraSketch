#!/usr/bin/env python
"""
Script de test simple pour l'API Anthropic Claude
"""
import os
from pathlib import Path

def test_anthropic_basic():
    """Test de base sans Django"""
    
    # Lire le fichier .env.local
    env_file = Path(__file__).parent / '.env.local'
    api_key = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    print("🚀 Test de connexion API Anthropic Claude")
    print("="*50)
    print(f"🔑 Clé API trouvée: {'✅ Oui' if api_key and api_key != 'sk-ant-your-key-here' else '❌ Non'}")
    
    if not api_key or api_key == 'sk-ant-your-key-here':
        print("\n⚠️  CONFIGURATION REQUISE:")
        print("📝 Pour configurer la clé API:")
        print("   1. Va sur https://console.anthropic.com/")
        print("   2. Crée une clé API")
        print("   3. Ouvre terrasketch/.env.local")
        print("   4. Remplace ANTHROPIC_API_KEY=sk-ant-your-key-here par ta clé")
        print("   5. Relance ce script")
        return False
    
    # Test avec le package anthropic
    try:
        import anthropic
        
        print("\n🧪 Test de connexion...")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test minimal avec modèle actuel
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Modèle par défaut
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Réponds juste 'OK Test réussi' pour confirmer."}
            ]
        )
        
        response = message.content[0].text
        print(f"📨 Réponse Claude: {response}")
        print("✅ Connexion API Anthropic réussie !")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        
        if "authentication" in str(e).lower():
            print("🔐 Problème d'authentification - clé API invalide")
        elif "rate" in str(e).lower():
            print("📊 Limite de débit atteinte")
        else:
            print("🔧 Autre erreur - vérifier réseau/configuration")
            
        return False

if __name__ == "__main__":
    success = test_anthropic_basic()
    
    if success:
        print("\n🎉 Prêt pour l'intégration complète !")
        print("▶️  Prochaine étape: Créer l'endpoint upload cadastre")
    else:
        print("\n🛠️  Résoudre la configuration avant de continuer")