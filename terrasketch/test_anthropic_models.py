#!/usr/bin/env python
"""
Test des modèles Anthropic disponibles
"""
import os
import anthropic
from pathlib import Path

def test_anthropic_models():
    """Test différents modèles Claude"""
    
    # Lire le fichier .env.local
    env_file = Path(__file__).parent / '.env.local'
    api_key = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    if not api_key or api_key == 'sk-ant-your-key-here':
        print("❌ Pas de clé API valide")
        return False
    
    print("🚀 Test modèles Anthropic Claude")
    print("="*40)
    
    # Liste modèles à tester (mars 2026)
    models_to_test = [
        "claude-3-5-sonnet-20241022",  # Version du projet
        "claude-3-5-sonnet-20250514",  # Version plus récente
        "claude-3-5-haiku-20241022",   # Version Haiku
        "claude-3-sonnet-20240229",    # Fallback
        "claude-3-haiku-20240307"      # Fallback économique
    ]
    
    client = anthropic.Anthropic(api_key=api_key)
    
    successful_models = []
    
    for model in models_to_test:
        try:
            print(f"\n🧪 Test modèle: {model}")
            
            message = client.messages.create(
                model=model,
                max_tokens=20,
                messages=[
                    {"role": "user", "content": "Réponds juste 'OK' pour confirmer."}
                ]
            )
            
            response = message.content[0].text.strip()
            print(f"✅ {model}: {response}")
            successful_models.append(model)
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not_found" in error_msg:
                print(f"❌ {model}: Modèle non disponible")
            elif "429" in error_msg:
                print(f"⚠️ {model}: Rate limit atteint")
            else:
                print(f"❌ {model}: {error_msg}")
    
    print(f"\n📊 Résultats:")
    print(f"✅ Modèles fonctionnels: {len(successful_models)}")
    
    if successful_models:
        print("📝 Modèles recommandés:")
        for model in successful_models[:3]:  # Top 3
            print(f"  - {model}")
        
        # Mise à jour config
        best_model = successful_models[0]
        print(f"\n🔧 Mettre à jour config avec: {best_model}")
        
        return best_model
    else:
        print("❌ Aucun modèle fonctionnel trouvé")
        return None

if __name__ == "__main__":
    best_model = test_anthropic_models()
    
    if best_model:
        print(f"\n🎉 Connexion API Anthropic validée!")
        print(f"🚀 Prêt pour génération IA avec {best_model}")
    else:
        print("\n🛠️ Vérifier clé API ou contacter Anthropic")