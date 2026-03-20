#!/usr/bin/env python3
"""
Script de test de l'intégration API IGN/Géoplateforme
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.cadastre_test')
django.setup()

from integrations.ign_api import IGNAPIService, enrich_parcelle_with_ign

def test_geocodage():
    """Test du service de géocodage IGN"""
    print("🗺️  Test du géocodage IGN")
    
    service = IGNAPIService()
    
    # Test avec une adresse de Paris
    address = "Place de la Bastille, Paris"
    result = service.geocode_address(address)
    
    if result:
        print(f"✅ Géocodage réussi :")
        print(f"   📍 Adresse: {result.address}")
        print(f"   🏙️  Ville: {result.city}")
        print(f"   📮 Code postal: {result.postal_code}")
        print(f"   📐 Coordonnées: {result.latitude:.6f}, {result.longitude:.6f}")
        print(f"   🎯 Précision: {result.accuracy}")
        return result.longitude, result.latitude
    else:
        print("❌ Échec du géocodage")
        return None, None

def test_altimetrie(longitude, latitude):
    """Test du service d'altimétrie IGN"""
    print("\n🏔️  Test de l'altimétrie IGN")
    
    if longitude is None or latitude is None:
        print("❌ Coordonnées manquantes, utilisation de coordonnées par défaut (Paris)")
        longitude, latitude = 2.3522, 48.8566
    
    service = IGNAPIService()
    topo_data = service.get_elevation_data(longitude, latitude)
    
    if topo_data:
        print(f"✅ Données topographiques récupérées :")
        print(f"   🔻 Altitude min: {topo_data.altitude_min:.1f}m")
        print(f"   🔺 Altitude max: {topo_data.altitude_max:.1f}m")
        print(f"   📏 Dénivelé: {topo_data.denivele_m:.1f}m")
        print(f"   📐 Pente moyenne: {topo_data.pente_moyenne_pct}%")
        print(f"   🏗️  Complexité terrassement: {topo_data.terrassement_complexite}")
    else:
        print("❌ Échec récupération données topographiques")

def test_cadastre_officiel(longitude, latitude):
    """Test du service cadastre officiel IGN"""
    print("\n🗂️  Test du cadastre officiel IGN")
    
    if longitude is None or latitude is None:
        print("❌ Coordonnées manquantes, test ignoré")
        return
    
    service = IGNAPIService()
    cadastre_data = service.get_cadastral_info(longitude, latitude)
    
    if cadastre_data:
        print(f"✅ Données cadastrales officielles récupérées :")
        print(f"   🆔 ID Parcelle: {cadastre_data.get('id_parcelle', 'N/A')}")
        print(f"   📍 Section: {cadastre_data.get('section', 'N/A')}")
        print(f"   🔢 Numéro: {cadastre_data.get('numero', 'N/A')}")
        print(f"   🏘️  Commune: {cadastre_data.get('commune', 'N/A')}")
        print(f"   📐 Surface officielle: {cadastre_data.get('surface_officielle', 'N/A')}")
        print(f"   🗂️  Source: {cadastre_data.get('source_type', 'N/A')}")
        if cadastre_data.get('all_properties'):
            print(f"   📋 Propriétés disponibles: {', '.join(cadastre_data['all_properties'].keys())}")
    else:
        print("⚠️  Pas de données cadastrales officielles disponibles")

def test_enrichissement_complet():
    """Test de l'enrichissement complet"""
    print("\n🔄 Test de l'enrichissement complet")
    
    # Coordonnées de test (Place de la Bastille, Paris)
    longitude, latitude = 2.3681, 48.8531
    address = "Place de la Bastille, Paris"
    
    print(f"📍 Test avec: {address}")
    print(f"🗺️  Coordonnées: {latitude:.6f}, {longitude:.6f}")
    
    result = enrich_parcelle_with_ign(longitude, latitude, address)
    
    print(f"\n📊 Résultat enrichissement IGN:")
    print(f"   ✅ Enrichi: {result['ign_enriched']}")
    
    if result.get('topographie'):
        topo = result['topographie']
        print(f"   🏔️  Topographie:")
        print(f"      - Altitude: {topo['altitude_min']:.1f}-{topo['altitude_max']:.1f}m")
        print(f"      - Dénivelé: {topo['denivele_m']:.1f}m")
        print(f"      - Pente: {topo['pente_moyenne_pct']}%")
        print(f"      - Complexité: {topo['terrassement_complexite']}")
    
    if result.get('geocode'):
        geo = result['geocode']
        print(f"   🗺️  Géocodage:")
        print(f"      - Adresse: {geo['address']}")
        print(f"      - Ville: {geo['city']}")
        print(f"      - Précision: {geo['accuracy']}")
    
    if result.get('cadastre_officiel'):
        cad = result['cadastre_officiel']
        print(f"   🗂️  Cadastre officiel:")
        print(f"      - Parcelle: {cad.get('id_parcelle', 'N/A')}")
        print(f"      - Commune: {cad.get('commune', 'N/A')}")
        print(f"      - Surface: {cad.get('surface_officielle', 'N/A')} m²")
        print(f"      - Source: {cad.get('source_type', 'N/A')}")
    
    if result.get('erreurs'):
        print(f"   ⚠️  Erreurs ({len(result['erreurs'])}):")
        for erreur in result['erreurs']:
            print(f"      - {erreur}")

if __name__ == "__main__":
    print("🚀 Test de l'intégration API IGN/Géoplateforme")
    print("=" * 50)
    
    try:
        # Test 1: Géocodage
        lon, lat = test_geocodage()
        
        # Test 2: Altimétrie
        test_altimetrie(lon, lat)
        
        # Test 3: Cadastre officiel
        test_cadastre_officiel(lon, lat)
        
        # Test 4: Enrichissement complet
        test_enrichissement_complet()
        
        print("\n🎉 Tests terminés !")
        
    except Exception as e:
        print(f"\n💥 Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)