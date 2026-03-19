"""
Vues API pour le module cadastre.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .uploads.handlers import handle_cadastre_upload
from .exceptions import (
    CadastreFormatNotSupportedError,
    CadastreParseError,
    CadastreGeometryError,
    CadastreFileTooLargeError
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class CadastreUploadView(APIView):
    """
    POST /api/cadastre/upload/
    
    Accepte un fichier multipart/form-data avec le champ "cadastre_file".
    
    Réponse succès (201) :
    {
        "id_parcelle": "750560000AB0012",
        "adresse_normalisee": null,
        "surface_m2": 312.5,
        "surface_ha": 0.031,
        "commune": "Paris",
        "source": "geojson",
        "geojson": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [...]},
            "properties": {"surface_m2": 312.5, "id_parcelle": "..."}
        },
        "topographie": {
            "altitude_min": 32.1,
            "altitude_max": 35.8,
            "denivele_m": 3.7,
            "pente_moyenne_pct": 4.2,
            "terrassement_complexite": "faible"
        }
    }

    Réponse erreur format non supporté (422) :
    {
        "error": "Les fichiers PDF et TIFF ne sont pas encore supportés.",
        "code": "FORMAT_NOT_SUPPORTED",
        "suggestion": "Utilisez la saisie d'adresse pour localiser votre parcelle."
    }

    Réponse erreur parsing (400) :
    {
        "error": "Impossible de lire le fichier. Vérifiez qu'il s'agit bien d'un fichier cadastral valide.",
        "code": "PARSE_ERROR",
        "detail": "..." // message technique, loggé côté serveur uniquement
    }
    """
    
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = []  # Pas d'auth pour MVP
    permission_classes = []      # Pas de permissions pour MVP
    
    def post(self, request, *args, **kwargs):
        """
        Traite l'upload d'un fichier cadastral.
        
        Args:
            request: Requête avec fichier en multipart/form-data
            
        Returns:
            Response: Résultat du parsing ou erreur
        """
        # Récupération du fichier
        cadastre_file = request.FILES.get('cadastre_file')
        if not cadastre_file:
            return Response({
                "error": "Aucun fichier fourni. Utilisez le champ 'cadastre_file'.",
                "code": "MISSING_FILE"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extraction user_id si authentification activée
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        try:
            # Traitement du fichier
            result = handle_cadastre_upload(cadastre_file, user_id)
            
            logger.info(f"Upload cadastre réussi: {cadastre_file.name} "
                       f"({cadastre_file.size / 1024 / 1024:.1f} MB) "
                       f"user_id={user_id}")
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except CadastreFormatNotSupportedError as e:
            # Format non supporté (PDF, TIFF, etc.)
            return Response({
                "error": "Format de fichier non supporté.",
                "code": "FORMAT_NOT_SUPPORTED",
                "detail": str(e),
                "suggestion": "Utilisez la saisie d'adresse pour localiser votre parcelle ou convertissez votre fichier en GeoJSON.",
                "formats_supportes": [
                    "GeoJSON (.json, .geojson)",
                    "Shapefile (.zip contenant .shp, .dbf, .shx)",
                    "DXF (.dxf)",
                    "EDIGÉO (.thf, .tar.bz2)"
                ]
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        except CadastreFileTooLargeError as e:
            # Fichier trop volumineux
            return Response({
                "error": "Fichier trop volumineux.",
                "code": "FILE_TOO_LARGE",
                "detail": str(e),
                "suggestion": "Réduisez la taille du fichier ou utilisez la saisie d'adresse."
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
        except CadastreGeometryError as e:
            # Géométrie invalide
            return Response({
                "error": "Géométrie de parcelle invalide.",
                "code": "INVALID_GEOMETRY",
                "detail": str(e),
                "suggestion": "Vérifiez que le fichier contient une géométrie de parcelle valide."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except CadastreParseError as e:
            # Erreur de parsing générale
            error_message = str(e)
            
            # Messages utilisateur selon le type d'erreur
            if "JSON" in error_message.upper():
                user_message = "Fichier JSON invalide. Vérifiez la syntaxe de votre fichier GeoJSON."
            elif "ZIP" in error_message.upper():
                user_message = "Archive ZIP corrompue ou ne contenant pas de fichier cadastral valide."
            elif "DXF" in error_message.upper():
                user_message = "Fichier DXF invalide. Assurez-vous qu'il contient des polygones de parcelles."
            elif "SHAPEFILE" in error_message.upper():
                user_message = "Fichier Shapefile invalide. Vérifiez qu'il contient les fichiers .shp, .dbf et .shx."
            else:
                user_message = "Impossible de lire le fichier. Vérifiez qu'il s'agit bien d'un fichier cadastral valide."
            
            return Response({
                "error": user_message,
                "code": "PARSE_ERROR",
                "suggestion": "Vérifiez le format et l'intégrité de votre fichier, ou utilisez la saisie d'adresse."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Erreur inattendue
            logger.error(f"Erreur inattendue upload cadastre: {cadastre_file.name} "
                        f"user_id={user_id} - {type(e).__name__}: {e}")
            
            return Response({
                "error": "Erreur interne du serveur lors du traitement du fichier.",
                "code": "INTERNAL_ERROR",
                "suggestion": "Réessayez ou contactez le support si le problème persiste."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CadastreStatusView(APIView):
    """
    GET /api/cadastre/status/
    
    Retourne le statut du module cadastre et les formats supportés.
    """
    
    authentication_classes = []  # Pas d'auth pour MVP
    permission_classes = []      # Pas de permissions pour MVP
    
    def get(self, request, *args, **kwargs):
        """
        Retourne les informations sur le module cadastre.
        
        Returns:
            Response: Statut du module et formats supportés
        """
        # Vérification disponibilité des librairies
        status_info = {
            "module": "cadastre",
            "version": "1.0.0",
            "status": "active"
        }
        
        # Test des librairies géospatiales
        libraries_status = {}
        
        try:
            import fiona
            libraries_status["fiona"] = {
                "available": True,
                "version": fiona.__version__ if hasattr(fiona, '__version__') else "unknown",
                "drivers": list(fiona.supported_drivers.keys())[:10]  # Premiers 10 drivers
            }
        except ImportError:
            libraries_status["fiona"] = {"available": False, "error": "Not installed"}
        
        try:
            import shapely
            libraries_status["shapely"] = {
                "available": True,
                "version": shapely.__version__ if hasattr(shapely, '__version__') else "unknown"
            }
        except ImportError:
            libraries_status["shapely"] = {"available": False, "error": "Not installed"}
        
        try:
            import pyproj
            libraries_status["pyproj"] = {
                "available": True,
                "version": pyproj.__version__ if hasattr(pyproj, '__version__') else "unknown"
            }
        except ImportError:
            libraries_status["pyproj"] = {"available": False, "error": "Not installed"}
        
        try:
            import ezdxf
            libraries_status["ezdxf"] = {
                "available": True,
                "version": ezdxf.__version__ if hasattr(ezdxf, '__version__') else "unknown"
            }
        except ImportError:
            libraries_status["ezdxf"] = {"available": False, "error": "Not installed"}
        
        # Formats supportés
        formats_supportes = [
            {
                "nom": "GeoJSON",
                "extensions": [".json", ".geojson"],
                "description": "Format standard pour données géographiques web",
                "source_typique": "Export QGIS, cadastre.data.gouv.fr"
            },
            {
                "nom": "Shapefile",
                "extensions": [".zip"],
                "description": "Archive contenant .shp, .dbf, .shx",
                "source_typique": "SIG collectivités, cadastre.data.gouv.fr"
            },
            {
                "nom": "DXF",
                "extensions": [".dxf"],
                "description": "Format CAO avec géométries parcelles",
                "source_typique": "DGFiP PCI, ArchiCAD, AutoCAD"
            },
            {
                "nom": "EDIGÉO",
                "extensions": [".thf", ".tar.bz2"],
                "description": "Format officiel cadastre français",
                "source_typique": "DGFiP PCI officiel"
            }
        ]
        
        # Vérification driver EDIGÉO
        edigeo_available = False
        if libraries_status.get("fiona", {}).get("available"):
            try:
                import fiona
                edigeo_available = "EDIGEO" in fiona.supported_drivers
            except:
                pass
        
        return Response({
            **status_info,
            "libraries": libraries_status,
            "formats_supportes": formats_supportes,
            "edigeo_driver": {
                "available": edigeo_available,
                "note": "Requis pour fichiers EDIGÉO (.thf)" if not edigeo_available else "Disponible"
            },
            "limits": {
                "max_file_size_mb": 50,
                "max_coordinates": 10000,
                "supported_projections": ["EPSG:4326", "EPSG:2154", "EPSG:3857"]
            }
        }, status=status.HTTP_200_OK)