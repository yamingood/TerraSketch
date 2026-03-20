"""
Module d'intégrations avec les APIs externes
"""

from .ign_api import IGNAPIService, enrich_parcelle_with_ign, TopographieData, GeocodeResult

__all__ = ['IGNAPIService', 'enrich_parcelle_with_ign', 'TopographieData', 'GeocodeResult']