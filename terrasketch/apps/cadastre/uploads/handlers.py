"""
Gestionnaire d'upload et traitement de fichiers cadastraux.
"""
import os
import tempfile
import logging
from typing import Dict, Any
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from ..exceptions import CadastreFileTooLargeError, CadastreParseError
from ..services.cadastre_parser import parse_cadastre_file
from .utils import validate_file_extension, get_file_size_mb

logger = logging.getLogger(__name__)

# Configuration par défaut
CADASTRE_MAX_SIZE_MB = getattr(settings, 'CADASTRE_UPLOAD_MAX_SIZE_MB', 50)


def handle_cadastre_upload(uploaded_file: UploadedFile, user_id: int = None) -> Dict[str, Any]:
    """
    Orchestre la réception et le traitement d'un fichier uploadé.
    
    Args:
        uploaded_file: Fichier uploadé via Django
        user_id: ID de l'utilisateur (optionnel pour MVP)
        
    Returns:
        dict: Résultat du parsing avec géométrie et métadonnées
        
    Raises:
        CadastreFileTooLargeError: Fichier trop volumineux
        CadastreParseError: Erreur de traitement
        
    Étapes :
    1. Vérifier la taille (max 50 Mo)
    2. Vérifier l'extension (whitelist : .json, .geojson, .zip, .dxf, .thf,
       .tar, .bz2) — rejeter tout autre type
    3. Sauvegarder dans un fichier temporaire (ne pas garder en mémoire)
    4. Appeler parse_cadastre_file()
    5. Enrichir avec API IGN altimétrie (get_elevation_grid + compute_terrain_diagnostics
       depuis ign_service.py)
    6. Sauvegarder en base via save_parcelle_to_db() (upsert sur id_parcelle si disponible)
    7. Supprimer le fichier temporaire
    8. Retourner le modèle Parcelle sauvegardé
    
    En cas d'erreur à n'importe quelle étape :
    - Supprimer le fichier temporaire (bloc finally)
    - Logger l'erreur avec le nom du fichier et le user_id
    - Propager l'exception avec un message utilisateur lisible
    """
    temp_file_path = None
    
    try:
        # 1. Vérification taille fichier
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > CADASTRE_MAX_SIZE_MB:
            raise CadastreFileTooLargeError(
                f"Fichier trop volumineux: {file_size_mb:.1f} MB. "
                f"Limite autorisée: {CADASTRE_MAX_SIZE_MB} MB"
            )
        
        # 2. Vérification extension
        if not validate_file_extension(uploaded_file.name):
            raise CadastreParseError(
                f"Extension de fichier non autorisée: {uploaded_file.name}. "
                "Formats acceptés: .json, .geojson, .zip, .dxf, .thf, .tar.bz2, .tar.gz"
            )
        
        # 3. Sauvegarde temporaire
        temp_file_path = _save_uploaded_file_to_temp(uploaded_file)
        
        # 4. Parsing du fichier
        logger.info(f"Début parsing fichier cadastral: {uploaded_file.name} "
                   f"({file_size_mb:.1f} MB) pour user_id={user_id}")
        
        result = parse_cadastre_file(temp_file_path)
        
        # 5. Enrichissement IGN asynchrone
        response = _format_api_response(result, uploaded_file.name)
        
        # Déclencher enrichissement IGN en arrière-plan (si activé)
        if getattr(settings, 'IGN_ENRICHMENT_ENABLED', True):
            _trigger_ign_enrichment(result['id_parcelle'], response['geojson'])
        
        # 6. Sauvegarde en base (Phase 2 - pour l'instant retour direct)
        # parcelle = _save_parcelle_to_db(result, uploaded_file.name, user_id)
        
        logger.info(f"Parsing réussi: {uploaded_file.name} -> "
                   f"Surface: {result.get('surface_m2', 0):.1f} m²")
        
        return response
        
    except Exception as e:
        # Log de l'erreur avec contexte
        logger.error(f"Erreur parsing cadastre: {uploaded_file.name if uploaded_file else 'unknown'} "
                    f"user_id={user_id} - {type(e).__name__}: {e}")
        
        # Propager l'exception
        raise
        
    finally:
        # 8. Nettoyage fichier temporaire
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError as e:
                logger.warning(f"Impossible de supprimer fichier temporaire {temp_file_path}: {e}")


def _save_uploaded_file_to_temp(uploaded_file: UploadedFile) -> str:
    """
    Sauvegarde un fichier uploadé dans un fichier temporaire.
    
    Args:
        uploaded_file: Fichier Django uploadé
        
    Returns:
        str: Chemin vers le fichier temporaire
        
    Raises:
        CadastreParseError: Erreur d'écriture
    """
    try:
        # Créer fichier temporaire avec extension préservée
        file_extension = os.path.splitext(uploaded_file.name)[1]
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extension,
            prefix='terrasketch_cadastre_'
        ) as temp_file:
            
            # Copier contenu par chunks pour économiser mémoire
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            
            return temp_file.name
            
    except Exception as e:
        raise CadastreParseError(f"Erreur sauvegarde fichier temporaire: {e}")


def _enrich_with_ign_data(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichit le résultat avec les données IGN altimétrie.
    
    Args:
        result: Résultat du parsing
        
    Returns:
        dict: Résultat enrichi avec topographie
        
    Note: Pour l'instant, simulation des données IGN.
    En Phase 2, intégrer avec le module IGN existant.
    """
    # Simulation données topographiques pour MVP
    # TODO: Intégrer avec apps.ign.services.ign_service
    
    geometry = result.get('geometry')
    if geometry:
        # Extraction coordonnées du centroïde pour simulation
        centroid = geometry.centroid
        
        # Simulation basique basée sur la position
        altitude_base = 50.0 + (centroid.y - 45.0) * 10  # Altitude simulée
        
        topographie = {
            "altitude_min": max(0, altitude_base - 2.0),
            "altitude_max": altitude_base + 3.0,
            "denivele_m": 5.0,
            "pente_moyenne_pct": 2.5,
            "terrassement_complexite": "faible"
        }
    else:
        # Valeurs par défaut si pas de géométrie
        topographie = {
            "altitude_min": None,
            "altitude_max": None,
            "denivele_m": None,
            "pente_moyenne_pct": None,
            "terrassement_complexite": "inconnu"
        }
    
    result['topographie'] = topographie
    return result


def _format_api_response(result: Dict[str, Any], original_filename: str) -> Dict[str, Any]:
    """
    Formate la réponse pour l'API REST.
    
    Args:
        result: Résultat enrichi du parsing
        original_filename: Nom du fichier original
        
    Returns:
        dict: Réponse formatée pour l'API
    """
    geometry = result.get('geometry')
    surface_m2 = result.get('surface_m2', 0)
    topographie = result.get('topographie', {})
    
    # Conversion geometry Shapely -> GeoJSON
    geojson_feature = None
    if geometry:
        try:
            geojson_feature = {
                "type": "Feature",
                "geometry": {
                    "type": geometry.geom_type,
                    "coordinates": list(geometry.exterior.coords) if hasattr(geometry, 'exterior') else []
                },
                "properties": {
                    "surface_m2": surface_m2,
                    "id_parcelle": result.get('id_parcelle'),
                    "commune": result.get('commune'),
                    "source": result.get('source'),
                    "fichier_original": original_filename
                }
            }
        except Exception as e:
            logger.warning(f"Erreur conversion GeoJSON: {e}")
    
    return {
        "id_parcelle": result.get('id_parcelle'),
        "adresse_normalisee": None,  # Pas disponible depuis fichier
        "surface_m2": surface_m2,
        "surface_ha": round(surface_m2 / 10000, 4) if surface_m2 else None,
        "commune": result.get('commune'),
        "section": result.get('section'),
        "numero": result.get('numero'),
        "source": result.get('source', 'upload'),
        "fichier_original": original_filename,
        "geojson": geojson_feature,
        "topographie": topographie,
        "parsing_info": {
            "code_insee": result.get('code_insee'),
            "geometry_type": geometry.geom_type if geometry else None,
            "coordinate_count": len(list(geometry.exterior.coords)) if geometry and hasattr(geometry, 'exterior') else 0
        }
    }


def _save_parcelle_to_db(result: Dict[str, Any], filename: str, user_id: int = None):
    """
    Sauvegarde la parcelle en base de données.
    
    Args:
        result: Résultat du parsing
        filename: Nom du fichier original
        user_id: ID utilisateur
        
    Returns:
        Parcelle: Instance sauvegardée
        
    Note: Implémentation Phase 2 quand le modèle Parcelle sera finalisé
    """
    # TODO: Implémenter sauvegarde avec le modèle Parcelle
    # from apps.cadastre.models import Parcelle
    # 
    # geometry = result.get('geometry')
    # parcelle_data = {
    #     'geom': geometry,
    #     'surface_m2': result.get('surface_m2'),
    #     'id_parcelle': result.get('id_parcelle'),
    #     'commune': result.get('commune'),
    #     'source_upload': result.get('source', 'upload'),
    #     'fichier_original': filename,
    #     'created_by_id': user_id
    # }
    # 
    # if result.get('id_parcelle'):
    #     # Upsert sur id_parcelle
    #     parcelle, created = Parcelle.objects.update_or_create(
    #         id_parcelle=result['id_parcelle'],
    #         defaults=parcelle_data
    #     )
    # else:
    #     # Création simple
    #     parcelle = Parcelle.objects.create(**parcelle_data)
    # 
    # return parcelle
    
    return None  # Placeholder pour MVP


def _trigger_ign_enrichment(parcel_id: str, geojson_data: Dict[str, Any]):
    """
    Déclenche l'enrichissement IGN en arrière-plan via Celery.
    
    Args:
        parcel_id: ID de la parcelle cadastrale
        geojson_data: Données GeoJSON de la parcelle
    """
    try:
        # Import local pour éviter les dépendances circulaires
        from apps.geography.tasks import enrich_with_ign
        
        # Déclencher la tâche Celery asynchrone
        task = enrich_with_ign.delay(parcel_id, geojson_data)
        
        logger.info(f"Tâche IGN déclenchée pour parcelle {parcel_id}: task_id={task.id}")
        
    except ImportError as e:
        logger.warning(f"Module geography non disponible - enrichissement IGN ignoré: {e}")
    except Exception as e:
        logger.error(f"Erreur déclenchement enrichissement IGN {parcel_id}: {e}")