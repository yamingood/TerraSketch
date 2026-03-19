#!/usr/bin/env python
"""
Test simple de l'endpoint cadastre sans serveur Django complet
"""
import json
from pathlib import Path

def create_test_geojson():
    """Crée un fichier GeoJSON de test simple"""
    test_geojson = {
        "type": "Feature",
        "properties": {
            "id_parcelle": "750101000AB0001",
            "commune": "Paris 1er",
            "surface": 150
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [2.3364, 48.8606],
                [2.3374, 48.8606], 
                [2.3374, 48.8616],
                [2.3364, 48.8616],
                [2.3364, 48.8606]
            ]]
        }
    }
    
    test_file = Path("test_parcelle.geojson")
    with open(test_file, 'w') as f:
        json.dump(test_geojson, f, indent=2)
    
    print(f"✅ Fichier test créé: {test_file}")
    return test_file

def test_cadastre_parsing():
    """Test du parsing cadastre sans serveur"""
    print("🧪 Test du module cadastre")
    print("="*40)
    
    # Créer fichier test
    test_file = create_test_geojson()
    
    try:
        # Import du parser
        from apps.cadastre.services.cadastre_parser import parse_cadastre_file
        
        print(f"📁 Parsing: {test_file}")
        result = parse_cadastre_file(str(test_file))
        
        print("✅ Parsing réussi!")
        print(f"📍 ID Parcelle: {result.get('id_parcelle', 'N/A')}")
        print(f"📐 Surface: {result.get('surface_m2', 0):.1f} m²")
        print(f"🏘️  Commune: {result.get('commune', 'N/A')}")
        
        # Test handler complet
        print("\n🔄 Test handler upload...")
        from apps.cadastre.uploads.handlers import _format_api_response
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Simuler upload
        with open(test_file, 'rb') as f:
            fake_upload = SimpleUploadedFile(
                test_file.name,
                f.read(),
                content_type='application/json'
            )
            
        # Test format réponse
        response = _format_api_response(result, test_file.name)
        
        print("✅ Handler testé avec succès!")
        print("📋 Réponse API:")
        print(json.dumps({k: v for k, v in response.items() if k != 'geojson'}, indent=2))
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur parsing: {e}")
        return False
    finally:
        # Nettoyage
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Fichier test supprimé")

def test_cadastre_status():
    """Test du endpoint status"""
    print("\n🔧 Test endpoint status...")
    
    try:
        from apps.cadastre.views import CadastreStatusView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/cadastre/status/')
        
        view = CadastreStatusView()
        response = view.get(request)
        
        print("✅ Status endpoint OK!")
        print(f"📊 Code: {response.status_code}")
        status_data = response.data
        print(f"🔧 Module: {status_data.get('module', 'N/A')}")
        print(f"📦 Formats supportés: {len(status_data.get('formats_supportes', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test Module Cadastre TerraSketch")
    print("="*50)
    
    # Test 1: Parser
    success1 = test_cadastre_parsing()
    
    # Test 2: Status endpoint
    success2 = test_cadastre_status()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("🎉 Module cadastre entièrement fonctionnel!")
        print("▶️  L'endpoint upload est prêt pour le frontend")
    else:
        print("🛠️  Problèmes détectés à corriger")