"""
Exceptions pour le module de parsing de fichiers cadastraux.
"""

class CadastreError(Exception):
    """Exception de base pour tous les erreurs du module cadastre."""
    pass


class CadastreFormatNotSupportedError(CadastreError):
    """Format de fichier non supporté (PDF, TIFF, inconnu)."""
    pass


class CadastreParseError(CadastreError):
    """Erreur de lecture/décodage du fichier."""
    pass


class CadastreGeometryError(CadastreError):
    """Géométrie invalide ou irrécupérable."""
    pass


class CadastreZipError(CadastreError):
    """Archive ZIP ne contient aucun format cadastral reconnu."""
    pass


class CadastreEdigeoError(CadastreError):
    """Erreur spécifique au parsing EDIGÉO."""
    pass


class CadastreEdigeoDriverError(CadastreEdigeoError):
    """Driver GDAL EDIGEO non disponible."""
    pass


class CadastreFileTooLargeError(CadastreError):
    """Fichier dépasse la limite autorisée."""
    pass