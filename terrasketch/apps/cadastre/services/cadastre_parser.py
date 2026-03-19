"""
Parseurs pour différents formats de fichiers cadastraux.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import fiona
    from shapely.geometry import Polygon, MultiPolygon, shape
    from pyproj import Transformer
    import ezdxf
    HAS_GEO_LIBS = True
except ImportError:
    HAS_GEO_LIBS = False

from ..uploads.utils import detect_file_type, extract_zip, extract_edigeo
from ..exceptions import (
    CadastreFormatNotSupportedError, CadastreParseError, 
    CadastreGeometryError, CadastreEdigeoDriverError
)
from .cadastre_validator import validate_parcelle_geometry


def parse_cadastre_file(file_path: str) -> Dict[str, Any]:
    """
    Point d'entrée unique du module de parsing.
    
    Args:
        file_path: Chemin vers le fichier à parser
        
    Returns:
        dict: Dictionnaire standardisé avec géométrie et métadonnées
        
    Algorithme :
    1. Détecter le type via detect_file_type()
    2. Si ZIP : extraire vers tmpdir, re-détecter le contenu, dispatcher
    3. Si EDIGEO archive : extraire .thf, appeler parse_edigeo()
    4. Dispatcher vers le bon parser selon le type détecté
    5. Valider le résultat via validate_parcelle_geometry()
    6. Retourner le dict standardisé
    
    Raises:
        CadastreFormatNotSupportedError: PDF, TIFF, format inconnu
        CadastreParseError: fichier corrompu ou vide
        CadastreGeometryError: géométrie invalide après parsing
    """
    if not HAS_GEO_LIBS:
        raise CadastreParseError(
            "Librairies géospatiales manquantes: fiona, shapely, pyproj, ezdxf"
        )
    
    file_type = detect_file_type(file_path)
    
    # Vérification format supporté
    if file_type == 'unknown':
        raise CadastreFormatNotSupportedError(
            "Format de fichier non reconnu. "
            "Formats supportés: GeoJSON, Shapefile (ZIP), DXF, EDIGEO"
        )
    
    temp_dir = None
    try:
        if file_type == 'zip':
            # Extraire et re-détecter
            temp_dir = tempfile.mkdtemp(prefix='terrasketch_cadastre_')
            extracted_file = extract_zip(file_path, temp_dir)
            file_type = detect_file_type(extracted_file)
            file_path = extracted_file
        
        elif file_type == 'edigeo' and not file_path.endswith('.thf'):
            # Archive EDIGEO, extraire le .thf
            temp_dir = tempfile.mkdtemp(prefix='terrasketch_edigeo_')
            thf_file = extract_edigeo(file_path, temp_dir)
            file_path = thf_file
        
        # Dispatcher vers le bon parser
        if file_type == 'geojson':
            result = parse_geojson(file_path)
        elif file_type == 'shapefile':
            result = parse_shapefile(file_path)
        elif file_type == 'dxf':
            result = parse_dxf(file_path)
        elif file_type == 'edigeo':
            result = parse_edigeo(file_path)
        else:
            raise CadastreFormatNotSupportedError(
                f"Format '{file_type}' non supporté dans cette version"
            )
        
        # Validation finale
        result = validate_parcelle_geometry(result)
        
        return result
        
    finally:
        # Nettoyage fichiers temporaires
        if temp_dir:
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def parse_geojson(file_path: str) -> Dict[str, Any]:
    """
    Lit un fichier GeoJSON cadastral (format Etalab ou IGN).
    
    Args:
        file_path: Chemin vers le fichier GeoJSON
        
    Returns:
        dict: Dictionnaire standardisé
        
    Cas à gérer :
    - FeatureCollection avec plusieurs features → prendre la feature
      de type Polygon avec la plus grande surface si plusieurs parcelles
    - Feature unique sans FeatureCollection wrapper
    - Coordonnées déjà en WGS84 (cas standard Etalab)
    - Champs Etalab : id, commune, contenance, section, numero
    - Champs IGN API Carto : id, nom_com, contenance, section, numero
    
    Vérifier que le CRS est bien WGS84. Si absent, supposer WGS84.
    Si CRS présent et différent (ex: Lambert93), reprojeter via pyproj.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CadastreParseError(f"Fichier GeoJSON invalide: {e}")
    except UnicodeDecodeError as e:
        raise CadastreParseError(f"Encodage du fichier GeoJSON non supporté: {e}")
    
    # Déterminer le CRS
    crs_code = _extract_crs_from_geojson(data)
    
    # Extraire les features
    features = []
    if data.get('type') == 'FeatureCollection':
        features = data.get('features', [])
    elif data.get('type') == 'Feature':
        features = [data]
    else:
        raise CadastreParseError(
            "Structure GeoJSON non reconnue. Attendu: FeatureCollection ou Feature"
        )
    
    if not features:
        raise CadastreParseError("Aucune feature trouvée dans le GeoJSON")
    
    # Filtrer les polygones et prendre le plus grand
    polygon_features = []
    for feature in features:
        geometry = feature.get('geometry', {})
        if geometry.get('type') in ['Polygon', 'MultiPolygon']:
            polygon_features.append(feature)
    
    if not polygon_features:
        raise CadastreParseError("Aucun polygone trouvé dans le GeoJSON")
    
    # Prendre la feature avec la plus grande surface
    largest_feature = max(polygon_features, key=lambda f: _estimate_feature_area(f))
    
    # Extraire géométrie et propriétés
    geometry_data = largest_feature['geometry']
    properties = largest_feature.get('properties', {})
    
    # Convertir en objet Shapely
    geometry = shape(geometry_data)
    
    # Reprojection si nécessaire
    if crs_code and crs_code != 4326:
        geometry = _reproject_geometry(geometry, crs_code, 4326)
    
    # Extraire métadonnées
    surface_m2 = _extract_surface_from_properties(properties)
    
    return {
        "geometry": geometry,
        "surface_m2": surface_m2,
        "id_parcelle": _extract_id_parcelle_from_properties(properties),
        "section": _extract_field_from_properties(properties, ['section', 'SECTION']),
        "numero": _extract_field_from_properties(properties, ['numero', 'NUMERO', 'number']),
        "code_insee": _extract_field_from_properties(properties, ['code_insee', 'CODE_INSEE']),
        "commune": _extract_field_from_properties(properties, ['commune', 'COMMUNE', 'nom_com', 'NOM_COM']),
        "source": "geojson"
    }


def parse_shapefile(shp_path: str) -> Dict[str, Any]:
    """
    Lit un fichier Shapefile cadastral via fiona.
    
    Args:
        shp_path: Chemin vers le fichier .shp
        
    Returns:
        dict: Dictionnaire standardisé
        
    Cas à gérer :
    - shp_path pointe vers le .shp (le .dbf et .shx doivent être dans le même répertoire)
    - CRS source = Lambert 93 (EPSG:2154) → reprojection WGS84 obligatoire
    - CRS source = WGS84 (EPSG:4326) → pas de reprojection
    - Plusieurs layers possibles : prendre le layer nommé "parcelle" ou "PARCELLE"
      Si absent, prendre le premier layer disponible
    - Attributs Etalab Shapefile : IDU, SECTION, NUMERO, NOM_COM, SUPF
    - Si SUPF absent, calculer la surface en Lambert93 avant reprojection
    
    La surface DOIT être calculée AVANT la reprojection vers WGS84
    (Lambert93 est en mètres, WGS84 en degrés → calcul de surface faux en WGS84).
    """
    try:
        # Ouvrir le shapefile
        with fiona.open(shp_path) as src:
            # Obtenir le CRS source
            crs_code = _extract_crs_code(src.crs)
            
            # Lire toutes les features
            features = list(src)
            
        if not features:
            raise CadastreParseError("Aucune feature trouvée dans le Shapefile")
        
        # Prendre la feature avec la plus grande surface
        largest_feature = max(features, key=lambda f: _estimate_feature_area_raw(f['geometry']))
        
        # Extraire géométrie et propriétés
        geometry = shape(largest_feature['geometry'])
        properties = largest_feature.get('properties', {})
        
        # Calculer la surface AVANT reprojection si en Lambert93
        surface_m2 = None
        if crs_code == 2154:  # Lambert93
            surface_m2 = geometry.area  # En m² car Lambert93 en mètres
        
        # Reprojection vers WGS84 si nécessaire
        if crs_code and crs_code != 4326:
            geometry = _reproject_geometry(geometry, crs_code, 4326)
        
        # Extraire surface depuis attributs si pas calculée
        if surface_m2 is None:
            surface_m2 = _extract_surface_from_properties(properties)
        
        return {
            "geometry": geometry,
            "surface_m2": surface_m2,
            "id_parcelle": _extract_field_from_properties(properties, ['IDU', 'idu', 'id']),
            "section": _extract_field_from_properties(properties, ['SECTION', 'section']),
            "numero": _extract_field_from_properties(properties, ['NUMERO', 'numero', 'number']),
            "code_insee": _extract_field_from_properties(properties, ['CODE_INSEE', 'code_insee']),
            "commune": _extract_field_from_properties(properties, ['NOM_COM', 'nom_com', 'commune']),
            "source": "shapefile"
        }
        
    except fiona.errors.DriverError as e:
        raise CadastreParseError(f"Erreur lecture Shapefile: {e}")
    except Exception as e:
        raise CadastreParseError(f"Erreur inattendue lors du parsing Shapefile: {e}")


def parse_dxf(dxf_path: str) -> Dict[str, Any]:
    """
    Lit un fichier DXF cadastral via ezdxf.
    
    Args:
        dxf_path: Chemin vers le fichier .dxf
        
    Returns:
        dict: Dictionnaire standardisé
        
    Spécificités DXF cadastral DGFiP :
    - Projection : Lambert CC 9 zones ou Lambert 93
      Détecter via le contenu du fichier (commentaire en en-tête) ou
      supposer Lambert 93 (EPSG:2154) par défaut
    - Entités à chercher (par ordre de priorité) :
        1. LWPOLYLINE sur layer "PARCELLE" ou "Parcelle"
        2. LWPOLYLINE sur layer "0"
        3. HATCH sur layer "PARCELLE"
        4. POLYLINE (ancien format DXF)
    - Prendre le polygone fermé avec la plus grande surface
    
    Calcul surface :
    - Calculer geom.area en Lambert93 (m²) AVANT reprojection WGS84
    
    Attributs :
    - L'identifiant parcelle peut être dans un MTEXT ou ATTRIB proche du polygone
    - Ne pas bloquer si introuvable : retourner id_parcelle=None
    
    Reprojection finale : Lambert93 (EPSG:2154) → WGS84 (EPSG:4326) via pyproj
    """
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Supposer Lambert93 par défaut (cas le plus courant)
        source_crs = 2154
        
        # Chercher des polygones par ordre de priorité
        polygons = []
        
        # 1. LWPOLYLINE sur layer PARCELLE
        for entity in msp.query('LWPOLYLINE[layer=="PARCELLE"]'):
            if entity.is_closed:
                coords = [(point[0], point[1]) for point in entity.get_points()]
                if len(coords) >= 4:  # Minimum pour un polygone
                    polygons.append(coords)
        
        # 2. LWPOLYLINE sur layer Parcelle (variante casse)
        if not polygons:
            for entity in msp.query('LWPOLYLINE[layer=="Parcelle"]'):
                if entity.is_closed:
                    coords = [(point[0], point[1]) for point in entity.get_points()]
                    if len(coords) >= 4:
                        polygons.append(coords)
        
        # 3. LWPOLYLINE sur layer 0 (fallback)
        if not polygons:
            for entity in msp.query('LWPOLYLINE[layer=="0"]'):
                if entity.is_closed:
                    coords = [(point[0], point[1]) for point in entity.get_points()]
                    if len(coords) >= 4:
                        polygons.append(coords)
        
        # 4. POLYLINE (ancien format)
        if not polygons:
            for entity in msp.query('POLYLINE'):
                if entity.is_closed:
                    coords = [(vertex.dxf.location[0], vertex.dxf.location[1]) 
                             for vertex in entity.vertices]
                    if len(coords) >= 4:
                        polygons.append(coords)
        
        if not polygons:
            raise CadastreParseError("Aucun polygone fermé trouvé dans le fichier DXF")
        
        # Créer des polygones Shapely et prendre le plus grand
        shapely_polygons = []
        for coords in polygons:
            try:
                polygon = Polygon(coords)
                if polygon.is_valid:
                    shapely_polygons.append(polygon)
            except Exception:
                continue
        
        if not shapely_polygons:
            raise CadastreParseError("Aucun polygone valide créé depuis les entités DXF")
        
        # Prendre le plus grand polygone
        largest_polygon = max(shapely_polygons, key=lambda p: p.area)
        
        # Calculer surface en Lambert93 (avant reprojection)
        surface_m2 = largest_polygon.area
        
        # Reprojection vers WGS84
        geometry_wgs84 = _reproject_geometry(largest_polygon, source_crs, 4326)
        
        # Chercher identifiant parcelle dans les MTEXT/ATTRIB (optionnel)
        id_parcelle = _extract_dxf_parcel_id(msp)
        
        return {
            "geometry": geometry_wgs84,
            "surface_m2": surface_m2,
            "id_parcelle": id_parcelle,
            "section": None,  # Rarement disponible dans DXF
            "numero": None,   # Rarement disponible dans DXF
            "code_insee": None,
            "commune": None,  # Rarement disponible dans DXF
            "source": "dxf"
        }
        
    except ezdxf.DXFStructureError as e:
        raise CadastreParseError(f"Fichier DXF corrompu: {e}")
    except Exception as e:
        raise CadastreParseError(f"Erreur lecture DXF: {e}")


def parse_edigeo(thf_path: str) -> Dict[str, Any]:
    """
    Lit un fichier EDIGÉO via fiona (driver GDAL EDIGEO).
    
    Args:
        thf_path: Chemin vers le fichier .thf déjà extrait
        
    Returns:
        dict: Dictionnaire standardisé
        
    Le paramètre thf_path est le chemin vers le fichier .thf déjà extrait
    (décompression gérée par extract_edigeo() dans utils.py).
    
    Layers EDIGÉO pertinents pour TerraSketch :
    - "PARCELLE" ou "PARCEL_id" → géométrie principale
    - "BATIMENT" → bâti (utile pour calcul emprise au sol, Phase 2)
    
    Attributs EDIGÉO standards :
    - IDU   → identifiant unique parcelle
    - SUPF  → surface en m²
    - SECTION, NUMERO, CODE_DEP, CODE_COM
    
    CRS source : RGF93/Lambert-93 (EPSG:2154)
    Reprojection : → WGS84 (EPSG:4326)
    
    Gestion des erreurs fiona/GDAL :
    - Si le driver EDIGEO n'est pas disponible (GDAL mal configuré),
      lever CadastreEdigeoDriverError avec message d'aide installation GDAL
    """
    # Vérifier disponibilité driver EDIGEO
    if "EDIGEO" not in fiona.supported_drivers:
        raise CadastreEdigeoDriverError(
            "Driver GDAL EDIGEO non disponible. "
            "Installez GDAL avec support EDIGEO complet. "
            "Sur Ubuntu: sudo apt-get install gdal-bin libgdal-dev. "
            "Sur macOS: brew install gdal"
        )
    
    try:
        # Lister les layers disponibles
        layers = fiona.listlayers(thf_path)
        
        # Chercher layer parcelle
        parcelle_layer = None
        for layer in layers:
            if layer.upper() in ['PARCELLE', 'PARCEL_ID', 'PARCELLES']:
                parcelle_layer = layer
                break
        
        if not parcelle_layer:
            # Prendre le premier layer par défaut
            if layers:
                parcelle_layer = layers[0]
            else:
                raise CadastreParseError("Aucun layer trouvé dans le fichier EDIGÉO")
        
        # Lire le layer parcelle
        with fiona.open(thf_path, layer=parcelle_layer) as src:
            features = list(src)
            crs_code = _extract_crs_code(src.crs)
        
        if not features:
            raise CadastreParseError(f"Aucune feature dans le layer {parcelle_layer}")
        
        # Prendre la feature avec la plus grande surface
        largest_feature = max(features, key=lambda f: _estimate_feature_area_raw(f['geometry']))
        
        # Extraire géométrie et propriétés
        geometry = shape(largest_feature['geometry'])
        properties = largest_feature.get('properties', {})
        
        # Surface depuis attributs EDIGEO
        surface_m2 = _extract_field_from_properties(properties, ['SUPF', 'supf', 'surface'])
        if surface_m2:
            try:
                surface_m2 = float(surface_m2)
            except (ValueError, TypeError):
                surface_m2 = None
        
        # Calculer surface si manquante et en Lambert93
        if surface_m2 is None and crs_code == 2154:
            surface_m2 = geometry.area
        
        # Reprojection vers WGS84
        if crs_code and crs_code != 4326:
            geometry = _reproject_geometry(geometry, crs_code, 4326)
        
        return {
            "geometry": geometry,
            "surface_m2": surface_m2,
            "id_parcelle": _extract_field_from_properties(properties, ['IDU', 'idu', 'id']),
            "section": _extract_field_from_properties(properties, ['SECTION', 'section']),
            "numero": _extract_field_from_properties(properties, ['NUMERO', 'numero']),
            "code_insee": _extract_field_from_properties(properties, ['CODE_COM', 'code_com']),
            "commune": None,  # Pas toujours disponible dans EDIGÉO
            "source": "edigeo"
        }
        
    except fiona.errors.DriverError as e:
        raise CadastreParseError(f"Erreur driver EDIGEO: {e}")
    except Exception as e:
        raise CadastreParseError(f"Erreur lecture EDIGÉO: {e}")


# Fonctions utilitaires privées

def _extract_crs_from_geojson(data: dict) -> Optional[int]:
    """Extrait le code CRS d'un GeoJSON."""
    crs = data.get('crs', {})
    if crs.get('type') == 'name':
        crs_name = crs.get('properties', {}).get('name', '')
        if 'EPSG:' in crs_name:
            try:
                return int(crs_name.split('EPSG:')[1])
            except (ValueError, IndexError):
                pass
    return 4326  # Défaut WGS84


def _extract_crs_code(crs_dict: dict) -> Optional[int]:
    """Extrait le code EPSG d'un dictionnaire CRS fiona."""
    if not crs_dict:
        return None
    
    # Format fiona typique: {'init': 'epsg:2154'}
    init = crs_dict.get('init', '')
    if init.startswith('epsg:'):
        try:
            return int(init.split(':')[1])
        except (ValueError, IndexError):
            pass
    
    # Autres formats possibles
    epsg = crs_dict.get('epsg')
    if epsg:
        try:
            return int(epsg)
        except ValueError:
            pass
    
    return None


def _reproject_geometry(geometry, source_crs: int, target_crs: int):
    """Reprojette une géométrie entre deux CRS."""
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    
    def transform_coords(coords):
        return [transformer.transform(x, y) for x, y in coords]
    
    if isinstance(geometry, Polygon):
        exterior = transform_coords(geometry.exterior.coords)
        holes = [transform_coords(interior.coords) for interior in geometry.interiors]
        return Polygon(exterior, holes)
    elif isinstance(geometry, MultiPolygon):
        transformed_polygons = []
        for poly in geometry.geoms:
            exterior = transform_coords(poly.exterior.coords)
            holes = [transform_coords(interior.coords) for interior in poly.interiors]
            transformed_polygons.append(Polygon(exterior, holes))
        return MultiPolygon(transformed_polygons)
    else:
        raise CadastreGeometryError(f"Type géométrie non supporté pour reprojection: {type(geometry)}")


def _estimate_feature_area(feature: dict) -> float:
    """Estime la surface d'une feature GeoJSON."""
    geometry = feature.get('geometry', {})
    return _estimate_feature_area_raw(geometry)


def _estimate_feature_area_raw(geometry_dict: dict) -> float:
    """Estime la surface d'une géométrie (dict coords)."""
    try:
        geom = shape(geometry_dict)
        return geom.area
    except Exception:
        return 0.0


def _extract_surface_from_properties(properties: dict) -> Optional[float]:
    """Extrait la surface depuis les propriétés."""
    surface_fields = ['contenance', 'surface', 'area', 'supf', 'SUPF', 'CONTENANCE']
    
    for field in surface_fields:
        value = properties.get(field)
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                continue
    
    return None


def _extract_id_parcelle_from_properties(properties: dict) -> Optional[str]:
    """Extrait l'identifiant parcelle depuis les propriétés."""
    id_fields = ['id', 'ID', 'idu', 'IDU', 'id_parcelle', 'parcelle_id']
    
    for field in id_fields:
        value = properties.get(field)
        if value:
            return str(value)
    
    return None


def _extract_field_from_properties(properties: dict, field_names: list) -> Optional[str]:
    """Extrait un champ depuis les propriétés avec plusieurs noms possibles."""
    for field in field_names:
        value = properties.get(field)
        if value is not None:
            return str(value)
    
    return None


def _extract_dxf_parcel_id(msp) -> Optional[str]:
    """Cherche un identifiant parcelle dans les textes DXF."""
    # Chercher dans les MTEXT et TEXT
    texts = []
    
    for entity in msp.query('MTEXT'):
        if hasattr(entity, 'text'):
            texts.append(entity.text)
    
    for entity in msp.query('TEXT'):
        if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
            texts.append(entity.dxf.text)
    
    # Chercher pattern identifiant parcelle (14 chiffres/lettres)
    import re
    for text in texts:
        # Pattern basique pour identifiant cadastral
        match = re.search(r'\b\d{5,6}\w{2,4}\d{3,4}\b', text)
        if match:
            return match.group(0)
    
    return None