"""
Tâches asynchrones Celery pour l'enrichissement IGN
"""
import logging
from typing import Dict, Any
import asyncio
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db import models

from .models import ParcelEnrichment, IGNUsageLog
from .services.ign_service import IGNService, IGNServiceError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_with_ign(self, parcel_id: str, geojson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichissement IGN en arrière-plan pour une parcelle
    
    Args:
        parcel_id: ID de la parcelle cadastrale
        geojson_data: Données GeoJSON de la parcelle
        
    Returns:
        Dict contenant les résultats d'enrichissement
    """
    logger.info(f"Début enrichissement IGN pour parcelle {parcel_id}")
    
    # Créer ou récupérer l'enregistrement d'enrichissement
    enrichment, created = ParcelEnrichment.objects.get_or_create(
        parcel_id=parcel_id,
        defaults={'status': 'processing'}
    )
    
    # Si pas créé et pas expiré, retourner les données existantes
    if not created and not enrichment.is_expired and enrichment.status == 'completed':
        logger.info(f"Données IGN existantes et valides pour parcelle {parcel_id}")
        return _serialize_enrichment_data(enrichment)
    
    # Marquer comme en traitement
    enrichment.status = 'processing'
    enrichment.save()
    
    try:
        # Initialiser le service IGN
        ign_service = IGNService()
        
        if not ign_service.enabled:
            logger.warning(f"Service IGN désactivé - enrichissement simulé pour {parcel_id}")
            return _create_simulated_enrichment(parcel_id, geojson_data, enrichment)
        
        # Enrichissement asynchrone via asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            enrichment_data = loop.run_until_complete(
                ign_service.enrich_parcelle_data(parcel_id, geojson_data)
            )
        finally:
            loop.close()
        
        # Sauvegarder les données enrichies
        _save_enrichment_data(enrichment, enrichment_data)
        enrichment.mark_as_completed()
        
        logger.info(f"Enrichissement IGN terminé avec succès pour parcelle {parcel_id}")
        
        # Notification temps réel (à implémenter avec WebSocket/SSE)
        _notify_enrichment_complete(parcel_id, enrichment_data)
        
        return _serialize_enrichment_data(enrichment)
        
    except IGNServiceError as e:
        logger.error(f"Erreur service IGN pour parcelle {parcel_id}: {e}")
        
        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retry {self.request.retries + 1}/{self.max_retries} dans {countdown}s")
            enrichment.retry_count += 1
            enrichment.save()
            raise self.retry(countdown=countdown)
        else:
            # Échec définitif - créer enrichissement simulé
            logger.error(f"Échec définitif IGN pour parcelle {parcel_id} - fallback simulé")
            enrichment.mark_as_failed(str(e))
            return _create_simulated_enrichment(parcel_id, geojson_data, enrichment)
            
    except Exception as e:
        logger.error(f"Erreur inattendue enrichissement IGN {parcel_id}: {e}")
        enrichment.mark_as_failed(f"Erreur inattendue: {e}")
        
        # Retry pour erreurs inattendues
        if self.request.retries < self.max_retries:
            countdown = 300 * (2 ** self.request.retries)  # 5min, 10min, 20min
            raise self.retry(countdown=countdown)
        
        # Fallback simulé en cas d'échec complet
        return _create_simulated_enrichment(parcel_id, geojson_data, enrichment)


def _save_enrichment_data(enrichment: ParcelEnrichment, data: Dict[str, Any]):
    """Sauvegarde les données d'enrichissement IGN"""
    
    # Données altimétriques
    elevation = data.get('elevation', {})
    enrichment.elevation_min = elevation.get('min')
    enrichment.elevation_max = elevation.get('max')
    enrichment.elevation_average = elevation.get('average')
    enrichment.elevation_profile = elevation.get('profile', [])
    enrichment.slope_analysis = elevation.get('slope_analysis', {})
    
    # Occupation du sol
    land_cover = data.get('land_cover', {})
    enrichment.land_cover_data = land_cover
    enrichment.vegetation_cover_pct = land_cover.get('vegetation_cover_pct')
    enrichment.artificial_cover_pct = land_cover.get('artificial_cover_pct')
    enrichment.water_cover_pct = land_cover.get('water_cover_pct')
    enrichment.agricultural_cover_pct = land_cover.get('agricultural_cover_pct')
    
    # Données administratives
    address = data.get('address', {})
    enrichment.address_normalized = address.get('normalized')
    enrichment.insee_code = address.get('insee_code')
    enrichment.department = address.get('department')
    enrichment.region = address.get('region')
    enrichment.quality_score = address.get('quality_score')
    
    # Contexte géographique
    context = data.get('geographic_context', {})
    enrichment.distance_to_water = context.get('distance_to_water_m')
    enrichment.distance_to_road = context.get('distance_to_major_road_m')
    enrichment.urban_density = context.get('urban_density')
    enrichment.climate_zone_ign = context.get('climate_zone')
    
    # Métadonnées
    enrichment.ign_data_version = data.get('data_version', '2024.1')
    enrichment.cache_expires_at = timezone.now() + timedelta(hours=24)
    
    enrichment.save()


def _create_simulated_enrichment(parcel_id: str, geojson_data: Dict[str, Any], 
                               enrichment: ParcelEnrichment) -> Dict[str, Any]:
    """Crée un enrichissement simulé en cas d'échec IGN"""
    
    logger.info(f"Création enrichissement simulé pour parcelle {parcel_id}")
    
    # Calculer le centroïde approximatif
    coordinates = geojson_data['geometry']['coordinates'][0]
    if coordinates:
        avg_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
        avg_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
    else:
        avg_lon, avg_lat = 2.3522, 48.8566  # Paris par défaut
    
    # Estimation basée sur les coordonnées
    simulated_data = {
        'parcel_id': parcel_id,
        'elevation': {
            'min': 30.0 + (avg_lat - 48) * 50,  # Variation selon latitude
            'max': 35.0 + (avg_lat - 48) * 50,
            'average': 32.5 + (avg_lat - 48) * 50,
            'profile': [
                {'distance': 0, 'elevation': 30.0 + (avg_lat - 48) * 50},
                {'distance': 10, 'elevation': 32.5 + (avg_lat - 48) * 50},
                {'distance': 20, 'elevation': 35.0 + (avg_lat - 48) * 50}
            ],
            'slope_analysis': {
                'max_slope_pct': 8.5,
                'average_slope_pct': 4.2,
                'areas': [
                    {'slope_range': '0-5%', 'area_pct': 75.0},
                    {'slope_range': '5-15%', 'area_pct': 25.0}
                ]
            }
        },
        'address': {
            'normalized': f"Parcelle {avg_lat:.4f}, {avg_lon:.4f}",
            'insee_code': '',
            'department': '75' if 2.0 <= avg_lon <= 2.6 and 48.8 <= avg_lat <= 49.0 else '00',
            'region': '11' if 2.0 <= avg_lon <= 2.6 and 48.8 <= avg_lat <= 49.0 else '00',
            'city': '',
            'postcode': '',
            'quality_score': 0.3
        },
        'land_cover': {
            'ocs_ge_version': '2022_simulated',
            'categories': [
                {'code': '131', 'label': 'Espaces verts urbains', 'area_pct': 65.0},
                {'code': '211', 'label': 'Zones résidentielles', 'area_pct': 35.0}
            ],
            'vegetation_cover_pct': 65.0,
            'artificial_cover_pct': 35.0,
            'water_cover_pct': 0.0,
            'agricultural_cover_pct': 0.0
        },
        'geographic_context': {
            'distance_to_water_m': 1200,
            'distance_to_major_road_m': 150,
            'urban_density': 'moderate',
            'climate_zone': 'Océanique dégradé (Cfb)'
        },
        'enriched_at': timezone.now().isoformat(),
        'data_version': '2024.1_simulated'
    }
    
    # Sauvegarder les données simulées
    _save_enrichment_data(enrichment, simulated_data)
    enrichment.mark_as_completed()
    
    return _serialize_enrichment_data(enrichment)


def _serialize_enrichment_data(enrichment: ParcelEnrichment) -> Dict[str, Any]:
    """Sérialise les données d'enrichissement pour la réponse"""
    return {
        'parcel_id': enrichment.parcel_id,
        'status': enrichment.status,
        'elevation': {
            'min': enrichment.elevation_min,
            'max': enrichment.elevation_max,
            'average': enrichment.elevation_average,
            'range': enrichment.elevation_range,
            'profile': enrichment.elevation_profile,
            'slope_analysis': enrichment.slope_analysis
        },
        'land_cover': {
            'data': enrichment.land_cover_data,
            'vegetation_pct': enrichment.vegetation_cover_pct,
            'artificial_pct': enrichment.artificial_cover_pct,
            'water_pct': enrichment.water_cover_pct,
            'agricultural_pct': enrichment.agricultural_cover_pct
        },
        'address': {
            'normalized': enrichment.address_normalized,
            'insee_code': enrichment.insee_code,
            'department': enrichment.department,
            'region': enrichment.region,
            'quality_score': enrichment.quality_score
        },
        'geographic_context': {
            'distance_to_water_m': enrichment.distance_to_water,
            'distance_to_road_m': enrichment.distance_to_road,
            'urban_density': enrichment.urban_density,
            'climate_zone': enrichment.climate_zone_ign
        },
        'metadata': {
            'enriched_at': enrichment.enriched_at.isoformat(),
            'updated_at': enrichment.updated_at.isoformat(),
            'data_version': enrichment.ign_data_version,
            'cache_expires_at': enrichment.cache_expires_at.isoformat(),
            'retry_count': enrichment.retry_count
        }
    }


def _notify_enrichment_complete(parcel_id: str, data: Dict[str, Any]):
    """Notification temps réel de completion d'enrichissement (WebSocket/SSE)"""
    
    # Pour MVP, on utilise le cache pour stocker les notifications
    # Dans une version complète, on utiliserait Django Channels/WebSocket
    
    notification = {
        'type': 'ign_enrichment_complete',
        'parcel_id': parcel_id,
        'timestamp': timezone.now().isoformat(),
        'data': {
            'status': 'completed',
            'elevation_range': f"{data['elevation']['min']:.1f}-{data['elevation']['max']:.1f}m",
            'vegetation_cover': f"{data['land_cover']['vegetation_cover_pct']:.1f}%",
            'address': data['address']['normalized']
        }
    }
    
    # Stocker dans le cache pour 5 minutes
    cache.set(f'ign_notification_{parcel_id}', notification, timeout=300)
    
    logger.info(f"Notification enrichissement IGN créée pour parcelle {parcel_id}")


@shared_task
def cleanup_expired_enrichments():
    """Tâche de nettoyage des enrichissements expirés"""
    
    cutoff_date = timezone.now() - timedelta(days=7)  # Garder 7 jours d'historique
    
    # Supprimer les enrichissements expirés anciens
    expired_count = ParcelEnrichment.objects.filter(
        cache_expires_at__lt=cutoff_date,
        status__in=['expired', 'failed']
    ).delete()[0]
    
    # Marquer comme expirés les enrichissements dépassés
    expired_enrichments = ParcelEnrichment.objects.filter(
        cache_expires_at__lt=timezone.now(),
        status='completed'
    )
    updated_count = expired_enrichments.update(status='expired')
    
    logger.info(f"Nettoyage enrichissements IGN: {expired_count} supprimés, {updated_count} expirés")
    
    return {
        'deleted': expired_count,
        'expired': updated_count
    }


@shared_task
def generate_ign_usage_report():
    """Génère un rapport d'utilisation IGN quotidien"""
    
    today = timezone.now().date()
    
    # Statistiques d'utilisation
    total_requests = IGNUsageLog.objects.filter(
        created_at__date=today
    ).count()
    
    successful_requests = IGNUsageLog.objects.filter(
        created_at__date=today,
        success=True
    ).count()
    
    failed_requests = total_requests - successful_requests
    
    # Répartition par endpoint
    endpoint_stats = IGNUsageLog.objects.filter(
        created_at__date=today
    ).values('endpoint').annotate(
        count=models.Count('id'),
        success_rate=models.Avg('success')
    ).order_by('-count')
    
    # Temps de réponse moyen
    avg_response_time = IGNUsageLog.objects.filter(
        created_at__date=today,
        success=True
    ).aggregate(
        avg_time=models.Avg('response_time_ms')
    )['avg_time'] or 0
    
    report = {
        'date': today.isoformat(),
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': round((successful_requests / max(total_requests, 1)) * 100, 2),
        'avg_response_time_ms': round(avg_response_time, 2),
        'endpoints': list(endpoint_stats)
    }
    
    # Stocker le rapport dans le cache
    cache.set(f'ign_usage_report_{today}', report, timeout=86400)  # 24h
    
    logger.info(f"Rapport d'utilisation IGN généré: {total_requests} requêtes, {successful_requests} succès")
    
    return report