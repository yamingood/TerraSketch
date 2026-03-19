"""
Validation et nettoyage de géométries extraites de fichiers cadastraux.
"""
from typing import Dict, Any

try:
    from shapely.geometry import Polygon, MultiPolygon
    from shapely import validation
    from pyproj import Transformer
    HAS_SHAPELY = True
    HAS_PYPROJ = True
except ImportError:
    HAS_SHAPELY = False
    HAS_PYPROJ = False

from ..exceptions import CadastreGeometryError


def validate_parcelle_geometry(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide et nettoie la géométrie extraite par un parser.
    
    Args:
        result: Dictionnaire retourné par un parser avec géométrie
        
    Returns:
        dict: Dictionnaire enrichi avec surface_m2 calculée si manquante
        
    Raises:
        CadastreGeometryError: Si la géométrie est irrécupérable
        
    Vérifications :
    1. La géométrie est un Polygon ou MultiPolygon valide (shapely .is_valid)
    2. Si MultiPolygon, prendre le plus grand Polygon
    3. Si invalide, tenter un buffer(0) pour corriger les auto-intersections
    4. Les coordonnées sont bien en WGS84 :
       - longitude entre -180 et 180
       - latitude entre -90 et 90
       - Pour la France métropolitaine : lon entre -5 et 10, lat entre 41 et 52
    5. Surface cohérente :
       - Minimum : 1 m² (éviter les artefacts)
       - Maximum : 500 000 m² = 50 ha (alerte si dépassé, pas d'erreur)
    6. Si surface_m2 est None, la calculer en projetant le polygone en
       Lambert93 (EPSG:2154) via pyproj puis calculer l'aire Shapely
    """
    if not HAS_SHAPELY or not HAS_PYPROJ:
        raise CadastreGeometryError(
            "Librairies shapely et pyproj requises pour la validation de géométrie"
        )
    
    geometry = result.get('geometry')
    if not geometry:
        raise CadastreGeometryError("Aucune géométrie trouvée dans le résultat")
    
    # 1. Vérification du type de géométrie
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        raise CadastreGeometryError(
            f"Type de géométrie non supporté: {type(geometry)}. "
            "Seuls Polygon et MultiPolygon sont acceptés."
        )
    
    # 2. Si MultiPolygon, prendre le plus grand polygon
    if isinstance(geometry, MultiPolygon):
        if len(geometry.geoms) == 0:
            raise CadastreGeometryError("MultiPolygon vide")
        
        # Prendre le polygone avec la plus grande surface
        largest_polygon = max(geometry.geoms, key=lambda p: p.area)
        geometry = largest_polygon
        result['geometry'] = geometry
    
    # 3. Validation et correction de la géométrie
    if not geometry.is_valid:
        # Tentative de correction avec buffer(0)
        try:
            corrected_geometry = geometry.buffer(0)
            if corrected_geometry.is_valid and isinstance(corrected_geometry, Polygon):
                geometry = corrected_geometry
                result['geometry'] = geometry
            else:
                raise CadastreGeometryError(
                    f"Géométrie invalide et non corrigeable: {validation.explain_validity(geometry)}"
                )
        except Exception as e:
            raise CadastreGeometryError(f"Erreur lors de la correction de géométrie: {e}")
    
    # 4. Validation des coordonnées WGS84
    _validate_wgs84_coordinates(geometry)
    
    # 5. Validation de la surface
    surface_m2 = result.get('surface_m2')
    if surface_m2 is None:
        # Calculer la surface en projetant vers Lambert93
        surface_m2 = _calculate_surface_lambert93(geometry)
        result['surface_m2'] = surface_m2
    
    # Vérification cohérence surface
    if surface_m2 < 1.0:
        raise CadastreGeometryError(
            f"Surface trop petite ({surface_m2:.2f} m²). "
            "Minimum requis: 1 m² pour éviter les artefacts."
        )
    
    # Avertissement pour surface très grande (pas d'erreur)
    if surface_m2 > 500000:  # 50 hectares
        import warnings
        warnings.warn(
            f"Surface très importante détectée: {surface_m2:.0f} m² "
            f"({surface_m2/10000:.1f} ha). Vérifiez la géométrie.",
            UserWarning
        )
    
    return result


def _validate_wgs84_coordinates(geometry: Polygon) -> None:
    """
    Valide que les coordonnées sont dans les limites WGS84 et France.
    
    Args:
        geometry: Polygon à valider
        
    Raises:
        CadastreGeometryError: Si les coordonnées sont hors limites
    """
    # Extraire toutes les coordonnées (exterior + holes)
    coords = list(geometry.exterior.coords)
    for interior in geometry.interiors:
        coords.extend(list(interior.coords))
    
    # Vérifier les limites globales WGS84
    for lon, lat in coords:
        if not (-180 <= lon <= 180):
            raise CadastreGeometryError(
                f"Longitude hors limites WGS84: {lon}. "
                "Attendu: -180 à 180 degrés."
            )
        if not (-90 <= lat <= 90):
            raise CadastreGeometryError(
                f"Latitude hors limites WGS84: {lat}. "
                "Attendu: -90 à 90 degrés."
            )
    
    # Vérifier les limites France métropolitaine (tolérance élargie)
    france_bounds = {
        'lon_min': -5.5, 'lon_max': 10.0,  # Inclut Corse et DOM-TOM proches
        'lat_min': 41.0, 'lat_max': 52.0   # Inclut nord de la France
    }
    
    for lon, lat in coords:
        if not (france_bounds['lon_min'] <= lon <= france_bounds['lon_max']):
            import warnings
            warnings.warn(
                f"Longitude hors zone France métropolitaine: {lon}. "
                f"Zone attendue: {france_bounds['lon_min']} à {france_bounds['lon_max']}. "
                "Vérifiez la projection du fichier source.",
                UserWarning
            )
        if not (france_bounds['lat_min'] <= lat <= france_bounds['lat_max']):
            import warnings
            warnings.warn(
                f"Latitude hors zone France métropolitaine: {lat}. "
                f"Zone attendue: {france_bounds['lat_min']} à {france_bounds['lat_max']}. "
                "Vérifiez la projection du fichier source.",
                UserWarning
            )


def _calculate_surface_lambert93(geometry_wgs84: Polygon) -> float:
    """
    Calcule la surface en m² d'un polygone en le reprojetant vers Lambert93.
    
    Args:
        geometry_wgs84: Polygon en coordonnées WGS84 (EPSG:4326)
        
    Returns:
        float: Surface en mètres carrés
        
    Raises:
        CadastreGeometryError: En cas d'erreur de reprojection
    """
    try:
        # Transformer WGS84 → Lambert93
        transformer = Transformer.from_crs(4326, 2154, always_xy=True)
        
        # Reprojeter les coordonnées
        exterior_coords = []
        for lon, lat in geometry_wgs84.exterior.coords:
            x, y = transformer.transform(lon, lat)
            exterior_coords.append((x, y))
        
        # Reprojeter les trous (holes)
        interior_coords = []
        for interior in geometry_wgs84.interiors:
            hole_coords = []
            for lon, lat in interior.coords:
                x, y = transformer.transform(lon, lat)
                hole_coords.append((x, y))
            interior_coords.append(hole_coords)
        
        # Créer le polygone en Lambert93
        geometry_lambert93 = Polygon(exterior_coords, holes=interior_coords)
        
        # Calculer l'aire en m²
        return geometry_lambert93.area
        
    except Exception as e:
        raise CadastreGeometryError(f"Erreur lors du calcul de surface: {e}")


def validate_parcelle_id(id_parcelle: str) -> bool:
    """
    Valide le format d'un identifiant parcellaire français.
    
    Args:
        id_parcelle: Identifiant à valider (ex: "750560000AB0012")
        
    Returns:
        bool: True si l'identifiant est valide
    """
    if not id_parcelle or not isinstance(id_parcelle, str):
        return False
    
    # Format standard: 14 caractères
    # - 5 chiffres code INSEE commune (ex: 75056)
    # - 3 chiffres préfixe (000)
    # - 2 lettres section (ex: AB)
    # - 4 chiffres numéro parcelle (ex: 0012)
    
    if len(id_parcelle) != 14:
        return False
    
    try:
        # Vérification structure
        code_insee = id_parcelle[:5]
        prefixe = id_parcelle[5:8]
        section = id_parcelle[8:10]
        numero = id_parcelle[10:14]
        
        # Code INSEE: 5 chiffres
        if not code_insee.isdigit():
            return False
        
        # Préfixe: généralement 000
        if not prefixe.isdigit():
            return False
        
        # Section: 2 lettres
        if not section.isalpha():
            return False
        
        # Numéro: 4 chiffres
        if not numero.isdigit():
            return False
        
        return True
        
    except Exception:
        return False