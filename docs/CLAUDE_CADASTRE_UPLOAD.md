# TerraSketch — Module Upload & Parsing Fichiers Cadastraux

## Contexte

Ce module permet aux utilisateurs de TerraSketch de déposer un fichier cadastral
directement dans l'application, en alternative à la saisie d'adresse.

L'objectif est d'extraire automatiquement la géométrie de la parcelle (polygone
WGS84) et sa surface, puis de la transmettre au pipeline IGN/IA existant.

---

## Formats supportés (par priorité d'implémentation)

| Priorité | Format      | Extension(s)              | Source typique                  | Difficulté |
|----------|-------------|---------------------------|---------------------------------|------------|
| 1        | GeoJSON     | `.json`, `.geojson`       | Etalab, export QGIS             | Facile     |
| 2        | Shapefile   | `.zip` (shp+dbf+shx)      | Etalab, SIG collectivité        | Moyen      |
| 3        | DXF         | `.dxf`                    | DGFiP PCI, ArchiCAD, AutoCAD    | Difficile  |
| 4        | EDIGÉO      | `.tar.bz2`, `.thf`        | DGFiP PCI officiel              | Très diff. |
| Phase 2  | PDF / TIFF  | `.pdf`, `.tiff`, `.tif`   | Notaire, mairie, scan papier    | OCR requis |

Les formats PDF et TIFF sont hors scope de cette implémentation.
Retourner un message d'erreur explicite avec redirection vers la saisie d'adresse.

---

## Stack technique

- **Backend** : Django + Django REST Framework
- **Parsing géo** : fiona, shapely, pyproj, ezdxf
- **Détection format** : python-magic
- **Décompression** : zipfile (stdlib), tarfile (stdlib)
- **Base de données** : PostgreSQL + PostGIS (django.contrib.gis)
- **Stockage temporaire** : Django default_storage (local en dev, R2 en prod)
- **Frontend** : React — composant upload + prévisualisation carte

---

## Dépendances Python à ajouter dans requirements.txt

```
fiona>=1.9.5
shapely>=2.0.3
pyproj>=3.6.1
ezdxf>=1.1.3
python-magic>=0.4.27
```

> Note : fiona nécessite GDAL installé sur le système.
> Sur Ubuntu : `sudo apt-get install gdal-bin libgdal-dev`
> Sur macOS : `brew install gdal`
> Dans le Dockerfile : `RUN apt-get install -y gdal-bin libgdal-dev`

---

## Variables d'environnement

Aucune variable spécifique à ce module.
Le module s'appuie sur les variables PostgreSQL et Cloudflare R2 déjà définies.

```
# Limites de fichier (optionnel, valeurs par défaut dans settings.py)
CADASTRE_UPLOAD_MAX_SIZE_MB=50
CADASTRE_UPLOAD_TMP_DIR=tmp/cadastre
```

---

## Schéma de données

Ce module réutilise la table `parcelles` définie dans CLAUDE_IGN.md.
Aucune migration supplémentaire n'est nécessaire.

Ajouter uniquement deux champs à la migration existante :

```sql
ALTER TABLE parcelles ADD COLUMN IF NOT EXISTS
    source_upload       VARCHAR(20) DEFAULT 'ign_api',
    -- Valeurs : 'ign_api' | 'geojson' | 'shapefile' | 'dxf' | 'edigeo'

    fichier_original    VARCHAR(255);
    -- Nom du fichier déposé par l'utilisateur, pour audit
```

---

## Structure des fichiers à créer

```
cadastre/
  services/
    ign_service.py              # existant (CLAUDE_IGN.md)
    cadastre_parser.py          # NOUVEAU — parsing multi-format
    cadastre_validator.py       # NOUVEAU — validation géométrie
  uploads/
    __init__.py
    handlers.py                 # NOUVEAU — gestion upload fichier
    utils.py                    # NOUVEAU — décompression, détection type
  views.py                      # à compléter — endpoint upload
  urls.py                       # à compléter — route upload
  tests/
    test_cadastre_parser.py     # NOUVEAU
    fixtures/
      sample_parcelle.geojson   # NOUVEAU — fichier de test
      sample_parcelle.dxf       # NOUVEAU — fichier de test (minimal)
```

---

## Tâche 1 — Utilitaires `cadastre/uploads/utils.py`

### 1.1 Détection du type de fichier

```python
def detect_file_type(file_path: str) -> str:
    """
    Détecte le format du fichier cadastral.
    Retourne: 'geojson' | 'shapefile' | 'dxf' | 'edigeo' | 'zip' | 'unknown'

    Stratégie de détection (dans l'ordre) :
    1. Extension du fichier (.geojson, .dxf, .thf, .tar.bz2, etc.)
    2. Contenu MIME via python-magic (premiers bytes)
    3. Tentative d'ouverture JSON (fallback pour .json ambigus)
    """
```

### 1.2 Décompression ZIP

```python
def extract_zip(zip_path: str, dest_dir: str) -> str:
    """
    Décompresse un .zip et retourne le chemin vers :
    - Le .shp si c'est un Shapefile
    - Le .geojson si c'est un GeoJSON zippé
    - Le .dxf si c'est un DXF zippé
    Lève: CadastreZipError si le ZIP ne contient aucun format reconnu
    """
```

### 1.3 Décompression EDIGÉO

```python
def extract_edigeo(archive_path: str, dest_dir: str) -> str:
    """
    Décompresse une archive EDIGÉO (.tar.bz2 ou .tar.gz).
    Retourne le chemin vers le fichier .thf (point d'entrée EDIGÉO).
    Lève: CadastreEdigeoError si le .thf est introuvable.

    Structure typique d'une archive EDIGÉO DGFiP :
      commune/
        feuille/
          *.thf        ← point d'entrée
          *.vec        ← données vectorielles (plusieurs fichiers)
          *.gen        ← données générales
    """
```

---

## Tâche 2 — Parsers `cadastre/services/cadastre_parser.py`

Implémenter les 4 parsers et l'orchestrateur principal.

### Interface de retour commune

Chaque parser doit retourner exactement ce dictionnaire :

```python
{
    "geometry":     Polygon,        # Shapely Polygon en WGS84 (EPSG:4326)
    "surface_m2":   float,          # Surface en m², None si non disponible
    "id_parcelle":  str | None,     # Identifiant cadastral (ex: "750560000AB0012")
    "section":      str | None,     # Section cadastrale (ex: "AB")
    "numero":       str | None,     # Numéro de parcelle (ex: "0012")
    "code_insee":   str | None,     # Code INSEE commune (ex: "75056")
    "commune":      str | None,     # Nom de la commune
    "source":       str,            # 'geojson' | 'shapefile' | 'dxf' | 'edigeo'
}
```

### 2.1 Parser GeoJSON

```python
def parse_geojson(file_path: str) -> dict:
    """
    Lit un fichier GeoJSON cadastral (format Etalab ou IGN).

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
```

### 2.2 Parser Shapefile

```python
def parse_shapefile(shp_path: str) -> dict:
    """
    Lit un fichier Shapefile cadastral via fiona.

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
```

### 2.3 Parser DXF

```python
def parse_dxf(dxf_path: str) -> dict:
    """
    Lit un fichier DXF cadastral via ezdxf.

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
```

### 2.4 Parser EDIGÉO

```python
def parse_edigeo(thf_path: str) -> dict:
    """
    Lit un fichier EDIGÉO via fiona (driver GDAL EDIGEO).

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
```

### 2.5 Orchestrateur principal

```python
def parse_cadastre_file(file_path: str) -> dict:
    """
    Point d'entrée unique du module de parsing.

    Algorithme :
    1. Détecter le type via detect_file_type()
    2. Si ZIP : extraire vers tmpdir, re-détecter le contenu, dispatcher
    3. Si EDIGEO archive : extraire .thf, appeler parse_edigeo()
    4. Dispatcher vers le bon parser selon le type détecté
    5. Valider le résultat via validate_parcelle_geometry()
    6. Retourner le dict standardisé

    Gestion tmpdir :
    - Créer un tempfile.TemporaryDirectory() pour les extractions
    - Nettoyer systématiquement dans un bloc finally

    Lève :
    - CadastreFormatNotSupportedError → PDF, TIFF, format inconnu
    - CadastreParseError              → fichier corrompu ou vide
    - CadastreGeometryError           → géométrie invalide après parsing
    """
```

---

## Tâche 3 — Validation `cadastre/services/cadastre_validator.py`

```python
def validate_parcelle_geometry(result: dict) -> dict:
    """
    Valide et nettoie la géométrie extraite par un parser.

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

    Retourne le dict enrichi avec surface_m2 calculée si manquante.
    Lève CadastreGeometryError si la géométrie est irrécupérable.
    """
```

---

## Tâche 4 — Gestionnaire d'upload `cadastre/uploads/handlers.py`

```python
def handle_cadastre_upload(uploaded_file, user_id: int) -> dict:
    """
    Orchestre la réception et le traitement d'un fichier uploadé.

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
```

---

## Tâche 5 — Endpoint DRF

Ajouter dans `cadastre/views.py` :

```python
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
```

Ajouter dans `cadastre/urls.py` :

```python
path("upload/", CadastreUploadView.as_view(), name="cadastre-upload"),
```

---

## Tâche 6 — Exceptions `cadastre/exceptions.py`

Ajouter ces exceptions au fichier existant (ou le créer s'il n'existe pas) :

```python
class CadastreError(Exception):
    """Base"""

class CadastreFormatNotSupportedError(CadastreError):
    """Format de fichier non supporté (PDF, TIFF, inconnu)"""

class CadastreParseError(CadastreError):
    """Erreur de lecture/décodage du fichier"""

class CadastreGeometryError(CadastreError):
    """Géométrie invalide ou irrécupérable"""

class CadastreZipError(CadastreError):
    """Archive ZIP ne contient aucun format cadastral reconnu"""

class CadastreEdigeoError(CadastreError):
    """Erreur spécifique au parsing EDIGÉO"""

class CadastreEdigeoDriverError(CadastreEdigeoError):
    """Driver GDAL EDIGEO non disponible"""

class CadastreFileTooLargeError(CadastreError):
    """Fichier dépasse la limite autorisée"""
```

---

## Tâche 7 — Composant React frontend

Créer `frontend/src/components/CadastreUpload.jsx` :

### Comportement attendu

```
État 1 — Idle
  Afficher une zone de drop avec les formats acceptés
  Bouton "Parcourir" + drag & drop

État 2 — Uploading
  Progress bar pendant l'envoi
  Message "Analyse du fichier cadastral..."

État 3 — Preview
  Carte (Leaflet ou Mapbox) centré sur la parcelle détectée
  Panneau latéral : surface, commune, id_parcelle, complexité terrassement
  Deux boutons : "Confirmer cette parcelle" | "Recommencer"

État 4 — Error
  Message d'erreur lisible (pas le stack trace)
  Si FORMAT_NOT_SUPPORTED : afficher le composant de saisie d'adresse
  Si PARSE_ERROR : afficher les formats supportés + lien vers cadastre.data.gouv.fr
```

### Props du composant

```jsx
<CadastreUpload
  onParcellConfirmed={(parcelle) => void}  // callback vers le flow IA
  onError={(error) => void}
  maxSizeMb={50}
/>
```

### Détails d'implémentation

- Utiliser `FormData` pour l'envoi multipart
- Afficher les formats acceptés : "GeoJSON · Shapefile (ZIP) · DXF · EDIGÉO"
- Valider la taille côté client avant envoi (éviter un aller-serveur inutile)
- Afficher le polygone de la parcelle sur la carte en overlay semi-transparent
  avec couleur verte (#2D6A4F, cohérent avec la charte Polsia/TerraSketch)
- Le bouton "Confirmer" appelle `onParcellConfirmed(parcelle)` avec le payload
  complet retourné par l'API (geojson + topographie)

---

## Tâche 8 — Tests

Créer `cadastre/tests/test_cadastre_parser.py` :

### Fixtures à créer

Créer `cadastre/tests/fixtures/` avec des fichiers de test minimaux :

```
sample_parcelle.geojson    # Feature simple, WGS84, surface ~300m²
sample_parcelle.dxf        # LWPOLYLINE sur layer PARCELLE, Lambert93
sample_multifeature.geojson # FeatureCollection avec 3 features → prendre la plus grande
```

### Tests unitaires

```
test_detect_geojson_by_extension
test_detect_geojson_by_content
test_detect_dxf_by_extension
test_detect_zip_by_extension

test_parse_geojson_simple
    → Charger sample_parcelle.geojson
    → Vérifier geometry est Polygon WGS84
    → Vérifier surface_m2 > 0

test_parse_geojson_multifeature
    → Charger sample_multifeature.geojson
    → Vérifier que la plus grande parcelle est retournée

test_parse_dxf_simple
    → Charger sample_parcelle.dxf
    → Vérifier geometry est Polygon WGS84
    → Vérifier lon entre -5 et 10, lat entre 41 et 52

test_parse_zip_shapefile
    → Créer un ZIP en mémoire contenant sample.shp + .dbf + .shx
    → Vérifier parsing correct

test_validate_geometry_invalid
    → Passer un Polygon auto-intersectant
    → Vérifier que buffer(0) corrige et retourne un Polygon valide

test_validate_surface_calculated_when_missing
    → Passer un résultat sans surface_m2
    → Vérifier que la surface est calculée et > 0

test_format_not_supported_pdf
    → Appeler parse_cadastre_file() avec un .pdf
    → Vérifier levée CadastreFormatNotSupportedError

test_parse_error_empty_file
    → Appeler parse_cadastre_file() avec un JSON vide {}
    → Vérifier levée CadastreParseError

test_upload_endpoint_success (APITestCase)
    → POST /api/cadastre/upload/ avec sample_parcelle.geojson
    → Mock get_elevation_grid() et compute_terrain_diagnostics()
    → Vérifier réponse 201 avec geojson et topographie

test_upload_endpoint_file_too_large (APITestCase)
    → POST avec fichier > 50 Mo (simulé)
    → Vérifier réponse 400

test_upload_endpoint_unsupported_format (APITestCase)
    → POST avec fichier .pdf
    → Vérifier réponse 422 avec code FORMAT_NOT_SUPPORTED
```

---

## Tâche 9 — Migration

Créer `cadastre/migrations/XXXX_add_upload_fields.py` :

Ajouter les champs `source_upload` et `fichier_original` à la table `parcelles`.

---

## Notes importantes

### Projection Lambert93

La **quasi-totalité** des fichiers cadastraux français sont en **Lambert 93
(EPSG:2154)**, pas en WGS84. La reprojection est obligatoire avant tout
stockage PostGIS ou affichage sur carte web.

```python
# Pattern de reprojection à utiliser systématiquement
from pyproj import Transformer
transformer = Transformer.from_crs(2154, 4326, always_xy=True)
# always_xy=True → garantit l'ordre (longitude, latitude) quelle que soit la version pyproj
```

### Calcul de surface

Toujours calculer la surface en m² **AVANT** la reprojection vers WGS84.
En WGS84 (degrés), `shapely.area` retourne des degrés carrés sans signification.

```python
# CORRECT
surface_m2 = geom_lambert93.area  # en m² car Lambert93 est en mètres

# INCORRECT
surface_m2 = geom_wgs84.area * 1e10  # approximation grossière, ne pas utiliser
```

### Fichiers Shapefile : toujours dans un ZIP

Les utilisateurs qui téléchargent depuis cadastre.data.gouv.fr reçoivent
un ZIP contenant au minimum `.shp`, `.dbf`, `.shx`.
Sans le `.dbf`, fiona ne peut pas lire les attributs.
Sans le `.shx`, fiona peut parfois lire mais c'est instable.
→ **Toujours demander le ZIP complet**, jamais le `.shp` seul.

### GDAL et EDIGÉO en production

Le driver GDAL pour EDIGÉO est `EDIGEO` (attention à la casse).
Vérifier sa disponibilité au démarrage de l'application :

```python
# Dans apps.py, méthode ready()
import fiona
if "EDIGEO" not in fiona.supported_drivers:
    import warnings
    warnings.warn(
        "Driver GDAL EDIGEO non disponible. "
        "Le parsing des fichiers EDIGÉO sera désactivé. "
        "Installer GDAL avec support EDIGEO."
    )
```

### Intégration avec le pipeline IA

Après parsing et validation, le service doit passer au module IA Claude
exactement le même `terrain_context` que défini dans CLAUDE_IGN.md :

```python
terrain_context = {
    "surface_m2":               parcelle.surface_m2,
    "denivele_m":               parcelle.denivele_m,
    "pente_moyenne_pct":        parcelle.pente_moyenne_pct,
    "terrassement_complexite":  parcelle.terrassement_complexite,
    "commune":                  parcelle.nom_commune,
    "geojson_parcelle":         parcelle.geom.geojson,
    "source":                   parcelle.source_upload,
}
```

Le pipeline IA est identique quelle que soit la source (upload fichier ou
saisie adresse). Le `terrain_context` est le contrat d'interface entre
ce module et le module de génération de plan.