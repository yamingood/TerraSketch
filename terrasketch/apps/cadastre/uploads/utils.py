"""
Utilitaires pour la détection de type et décompression de fichiers cadastraux.
"""
import json
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

from ..exceptions import CadastreZipError, CadastreEdigeoError


def detect_file_type(file_path: str) -> str:
    """
    Détecte le format du fichier cadastral.
    
    Args:
        file_path: Chemin vers le fichier à analyser
        
    Returns:
        str: 'geojson' | 'shapefile' | 'dxf' | 'edigeo' | 'zip' | 'unknown'
        
    Stratégie de détection (dans l'ordre) :
    1. Extension du fichier (.geojson, .dxf, .thf, .tar.bz2, etc.)
    2. Contenu MIME via python-magic (premiers bytes)
    3. Tentative d'ouverture JSON (fallback pour .json ambigus)
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    # 1. Détection par extension
    if extension in ['.geojson']:
        return 'geojson'
    elif extension in ['.json']:
        # Fallback vers test JSON pour distinguer GeoJSON vs autre JSON
        if _is_geojson_content(file_path):
            return 'geojson'
        return 'unknown'
    elif extension in ['.zip']:
        return 'zip'
    elif extension in ['.dxf']:
        return 'dxf'
    elif extension in ['.thf']:
        return 'edigeo'
    elif file_path.name.endswith('.tar.bz2') or file_path.name.endswith('.tar.gz'):
        return 'edigeo'
    
    # 2. Détection par contenu MIME (si python-magic disponible)
    if HAS_MAGIC:
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            if mime_type == 'application/zip':
                return 'zip'
            elif mime_type == 'application/json':
                if _is_geojson_content(file_path):
                    return 'geojson'
            elif mime_type in ['application/x-tar', 'application/x-bzip2', 'application/gzip']:
                return 'edigeo'
        except Exception:
            pass
    
    # 3. Tentative d'ouverture JSON en dernière chance
    if extension in ['.json'] or not extension:
        if _is_geojson_content(file_path):
            return 'geojson'
    
    return 'unknown'


def _is_geojson_content(file_path: Path) -> bool:
    """
    Vérifie si le contenu d'un fichier est du GeoJSON valide.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        bool: True si le fichier contient du GeoJSON valide
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Vérification structure GeoJSON basique
        if isinstance(data, dict):
            if data.get('type') == 'FeatureCollection' and 'features' in data:
                return True
            elif data.get('type') == 'Feature' and 'geometry' in data:
                return True
            elif data.get('type') in ['Polygon', 'MultiPolygon'] and 'coordinates' in data:
                return True
                
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        pass
        
    return False


def extract_zip(zip_path: str, dest_dir: str) -> str:
    """
    Décompresse un .zip et retourne le chemin vers le fichier principal.
    
    Args:
        zip_path: Chemin vers le fichier ZIP
        dest_dir: Répertoire de destination
        
    Returns:
        str: Chemin vers le fichier principal trouvé
        
    Raises:
        CadastreZipError: Si aucun format reconnu n'est trouvé
    """
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(dest_dir)
            
        # Chercher les fichiers par ordre de priorité
        extracted_files = list(dest_path.rglob('*'))
        
        # 1. Chercher .shp (Shapefile)
        for file_path in extracted_files:
            if file_path.suffix.lower() == '.shp':
                # Vérifier que les fichiers obligatoires .dbf et .shx existent
                base_path = file_path.with_suffix('')
                if (base_path.with_suffix('.dbf').exists() and 
                    base_path.with_suffix('.shx').exists()):
                    return str(file_path)
        
        # 2. Chercher .geojson ou .json
        for file_path in extracted_files:
            if file_path.suffix.lower() in ['.geojson', '.json']:
                if _is_geojson_content(file_path):
                    return str(file_path)
        
        # 3. Chercher .dxf
        for file_path in extracted_files:
            if file_path.suffix.lower() == '.dxf':
                return str(file_path)
                
    except zipfile.BadZipFile as e:
        raise CadastreZipError(f"Archive ZIP corrompue: {e}")
    except Exception as e:
        raise CadastreZipError(f"Erreur lors de l'extraction du ZIP: {e}")
    
    raise CadastreZipError(
        "Aucun format cadastral reconnu dans l'archive ZIP. "
        "Formats acceptés: Shapefile (.shp+.dbf+.shx), GeoJSON (.json/.geojson), DXF (.dxf)"
    )


def extract_edigeo(archive_path: str, dest_dir: str) -> str:
    """
    Décompresse une archive EDIGÉO (.tar.bz2 ou .tar.gz).
    
    Args:
        archive_path: Chemin vers l'archive EDIGÉO
        dest_dir: Répertoire de destination
        
    Returns:
        str: Chemin vers le fichier .thf (point d'entrée EDIGÉO)
        
    Raises:
        CadastreEdigeoError: Si le .thf est introuvable
        
    Structure typique d'une archive EDIGÉO DGFiP :
      commune/
        feuille/
          *.thf        ← point d'entrée
          *.vec        ← données vectorielles (plusieurs fichiers)
          *.gen        ← données générales
    """
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Détecter le mode de compression
        if archive_path.endswith('.tar.bz2'):
            mode = 'r:bz2'
        elif archive_path.endswith('.tar.gz'):
            mode = 'r:gz'
        else:
            mode = 'r'
            
        with tarfile.open(archive_path, mode) as tar:
            tar.extractall(dest_dir)
            
        # Chercher le fichier .thf
        thf_files = list(dest_path.rglob('*.thf'))
        
        if not thf_files:
            raise CadastreEdigeoError(
                "Fichier .thf introuvable dans l'archive EDIGÉO. "
                "L'archive doit contenir le point d'entrée .thf."
            )
        
        # Prendre le premier .thf trouvé
        return str(thf_files[0])
        
    except tarfile.TarError as e:
        raise CadastreEdigeoError(f"Archive EDIGÉO corrompue: {e}")
    except Exception as e:
        raise CadastreEdigeoError(f"Erreur lors de l'extraction de l'archive EDIGÉO: {e}")


def get_file_size_mb(file_path: str) -> float:
    """
    Retourne la taille du fichier en MB.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        float: Taille en mégaoctets
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def validate_file_extension(filename: str) -> bool:
    """
    Valide l'extension du fichier selon la whitelist.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        bool: True si l'extension est autorisée
    """
    allowed_extensions = {
        '.json', '.geojson', '.zip', '.dxf', '.thf',
        '.tar', '.bz2', '.gz'
    }
    
    filename_lower = filename.lower()
    
    # Cas spéciaux pour les extensions composées
    if filename_lower.endswith('.tar.bz2') or filename_lower.endswith('.tar.gz'):
        return True
    
    # Extension simple
    extension = Path(filename).suffix.lower()
    return extension in allowed_extensions