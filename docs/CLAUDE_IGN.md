# TerraSketch — Intégration API IGN Géoplateforme

## Contexte

Ce module intègre les APIs IGN (Géoplateforme) dans TerraSketch pour alimenter
deux fonctionnalités clés :

1. **Flux cadastral** — point d'entrée UX différenciateur de TerraSketch :
   l'utilisateur saisit une adresse et obtient la géométrie exacte de sa parcelle
2. **Diagnostic terrassement** — analyse du relief de la parcelle via altimétrie
   RGE ALTI® pour calculer les pentes, volumes de déblais/remblais et identifier
   les zones problématiques

**Aucune clé API requise.** Toutes les APIs IGN Géoplateforme sont ouvertes et
gratuites depuis 2024. Base URL : `https://data.geopf.fr` et `https://apicarto.ign.fr`

---

## Stack technique

- **Backend** : Django + Django REST Framework
- **Base de données** : PostgreSQL + PostGIS
- **Librairies géospatiales** : `shapely`, `pyproj`, `numpy`
- **HTTP** : `requests` avec retry automatique
- **Celery** : pour les tâches asynchrones (calcul altimétrique long)

---

## Variables d'environnement requises

```
DATABASE_URL=postgresql://user:password@localhost:5432/terrasketch
# Pas de clé API IGN nécessaire
```

---

## Rate limits IGN à respecter dans tout le code

```python
RATE_LIMITS = {
    "geocodage":      50,   # req/s
    "autocompletion": 10,   # req/s
    "altimetrie":      5,   # req/s
    "cadastre":       10,   # req/s (estimation prudente, non documenté)
}
# Toujours ajouter time.sleep(1 / RATE_LIMIT) entre les appels en boucle
```

---

## Architecture des fichiers à créer

```
terrasketch/
  ign/
    __init__.py
    client.py           # Client HTTP bas niveau (retry, rate limiting)
    geocodage.py        # Service de géocodage et autocomplétion
    cadastre.py         # Service de récupération des parcelles
    altimetrie.py       # Service de calcul altimétrique et pentes
    diagnostics.py      # Logique métier : analyse terrassement
    serializers.py      # DRF serializers pour les réponses IGN
    exceptions.py       # Exceptions métier IGN
    tests/
      test_geocodage.py
      test_cadastre.py
      test_altimetrie.py
      test_diagnostics.py
  api/
    views/
      parcelle_views.py     # Endpoints REST pour le frontend React
    urls/
      parcelle_urls.py
```

---

## Schéma PostgreSQL / PostGIS à créer

```sql
CREATE TABLE IF NOT EXISTS parcelles (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER REFERENCES users(id),

    -- Identifiants IGN
    id_parcelle             VARCHAR(20),        -- ex: 750560000AB0012
    code_insee              VARCHAR(5),
    section                 VARCHAR(10),
    numero                  VARCHAR(10),
    nom_commune             VARCHAR(100),
    prefixe                 VARCHAR(5),

    -- Géométrie PostGIS
    geom                    GEOMETRY(POLYGON, 4326),   -- WGS84
    surface_m2              DECIMAL(12, 2),

    -- Adresse de référence (saisie utilisateur)
    adresse_saisie          TEXT,
    lon                     DECIMAL(10, 7),
    lat                     DECIMAL(10, 7),

    -- Altimétrie (rempli après calcul async Celery)
    altitude_min            DECIMAL(8, 2),
    altitude_max            DECIMAL(8, 2),
    altitude_moyenne        DECIMAL(8, 2),
    pente_max_degres        DECIMAL(6, 2),
    pente_moyenne_degres    DECIMAL(6, 2),
    relief_data             JSONB,              -- grille complète {lon, lat, z}[]

    -- Diagnostic terrassement
    terrassement_requis     BOOLEAN DEFAULT FALSE,
    volume_deblai_m3        DECIMAL(10, 2),
    volume_remblai_m3       DECIMAL(10, 2),
    zones_pente_forte       JSONB,              -- GeoJSON polygones zones > seuil

    -- Métadonnées
    ign_fetched_at          TIMESTAMP,
    alti_computed_at        TIMESTAMP,
    alti_status             VARCHAR(10) DEFAULT 'pending', -- pending|ready|error
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_parcelles_geom      ON parcelles USING GIST(geom);
CREATE INDEX idx_parcelles_user      ON parcelles(user_id);
CREATE INDEX idx_parcelles_code_insee ON parcelles(code_insee);
```

---

## Tâche 1 — Client HTTP (`ign/client.py`)

Créer un client HTTP réutilisable avec :

```python
"""
Client HTTP bas niveau pour les APIs IGN Géoplateforme.
Gère : retry automatique, rate limiting, logging, timeouts.
"""

IGN_ENDPOINTS = {
    "geocodage_search":     "https://data.geopf.fr/geocodage/search",
    "geocodage_reverse":    "https://data.geopf.fr/geocodage/reverse",
    "autocompletion":       "https://data.geopf.fr/geocodage/completion",
    "cadastre_parcelle":    "https://apicarto.ign.fr/api/cadastre/parcelle",
    "altimetrie_elevation": "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json",
}

class IGNClient:
    """
    Comportement attendu :
    - Retry 3 fois sur HTTP 429, 503, 504 avec backoff exponentiel (1s, 2s, 4s)
    - Timeout 10s sur tous les appels
    - Logger chaque appel (url, params, status, durée) en DEBUG
    - Lever IGNRateLimitError si encore 429 après 3 retries
    - Lever IGNServiceUnavailableError si 503/504 après 3 retries
    - Lever IGNNotFoundError si 404
    - Méthode : get(endpoint_key, params) -> dict (JSON parsé)
    - Méthode : post(endpoint_key, json_body) -> dict (JSON parsé)
    """
```

Créer dans `ign/exceptions.py` :
```python
class IGNError(Exception): pass
class IGNGeocodeError(IGNError): pass
class IGNCadastreNotFoundError(IGNError): pass
class IGNRateLimitError(IGNError): pass
class IGNServiceUnavailableError(IGNError): pass
```

---

## Tâche 2 — Service de géocodage (`ign/geocodage.py`)

### 2a. Géocodage direct (adresse → coordonnées)

```python
def geocode_address(address: str) -> dict:
    """
    Convertit une adresse textuelle en coordonnées GPS.

    Appel :
    GET https://data.geopf.fr/geocodage/search
        ?q={address}&limit=1&type=housenumber,street,municipality

    Retourner :
    {
        "lon": float,
        "lat": float,
        "label": str,       # adresse normalisée IGN
        "score": float,     # confiance 0-1
        "city": str,
        "postcode": str,
        "context": str,     # département, région
        "type": str,        # housenumber | street | municipality
    }

    Lever IGNGeocodeError si aucun résultat ou score < 0.5
    """
```

### 2b. Autocomplétion (pour le champ de saisie React)

```python
def autocomplete_address(text: str, limit: int = 5) -> list[dict]:
    """
    Suggestions d'adresses en temps réel.

    Appel :
    GET https://data.geopf.fr/geocodage/completion
        ?text={text}&type=housenumber,street&maximumResponses={limit}

    Retourner :
    [{"label": str, "x": float, "y": float}, ...]

    Utilisé par : GET /api/parcelle/autocomplete/?q=...
    IMPORTANT : le frontend doit debouncer à 300ms minimum avant d'appeler
    cet endpoint, car la limite IGN est 10 req/s.
    """
```

### 2c. Géocodage inverse (clic carte → adresse)

```python
def reverse_geocode(lon: float, lat: float) -> dict:
    """
    Retrouve l'adresse la plus proche d'un point GPS.
    Utile si l'utilisateur clique directement sur une carte Leaflet/Mapbox.

    Appel :
    GET https://data.geopf.fr/geocodage/reverse
        ?lon={lon}&lat={lat}&type=housenumber,parcel

    Même format de retour que geocode_address().
    """
```

---

## Tâche 3 — Service cadastral (`ign/cadastre.py`)

### 3a. Parcelle par coordonnées GPS

```python
def get_parcelle_from_coords(lon: float, lat: float) -> dict:
    """
    Récupère la parcelle cadastrale PCI Express contenant un point GPS.

    Appel :
    GET https://apicarto.ign.fr/api/cadastre/parcelle
        ?geom={"type":"Point","coordinates":[{lon},{lat}]}&_limit=1

    Extraire Feature[0] de la FeatureCollection IGN et retourner :
    {
        "id_parcelle":  str,    # ex: "750560000AB0012"
        "code_insee":   str,
        "section":      str,
        "numero":       str,
        "prefixe":      str,
        "nom_commune":  str,
        "surface_m2":   float,  # champ "contenance" IGN en m²
        "geometry":     dict,   # GeoJSON Polygon WGS84
    }

    Lever IGNCadastreNotFoundError si aucune parcelle trouvée.
    """
```

### 3b. Parcelle par identifiant cadastral

```python
def get_parcelle_by_id(code_insee: str, section: str, numero: str) -> dict:
    """
    Appel :
    GET https://apicarto.ign.fr/api/cadastre/parcelle
        ?code_insee={code_insee}&section={section}&numero={numero}

    Même format de retour que get_parcelle_from_coords().
    """
```

### 3c. Flux complet adresse → parcelle (fonction principale TerraSketch)

```python
def get_parcelle_from_address(address: str) -> dict:
    """
    Flux principal — enchaîne géocodage + cadastre :
    1. geocode_address(address) -> lon, lat
    2. get_parcelle_from_coords(lon, lat) -> géométrie + surface
    3. Calculer bbox [lon_min, lat_min, lon_max, lat_max] depuis geometry

    Retourner tout dans un objet unifié :
    {
        "adresse_normalisee": str,
        "lon": float,
        "lat": float,
        "score_geocodage": float,
        "id_parcelle": str,
        "code_insee": str,
        "section": str,
        "numero": str,
        "nom_commune": str,
        "surface_m2": float,
        "geometry": dict,       # GeoJSON Polygon
        "bbox": list[float],    # [lon_min, lat_min, lon_max, lat_max]
    }
    """
```

### 3d. Sauvegarde PostGIS

```python
def save_parcelle_to_db(user_id: int, parcelle_data: dict) -> object:
    """
    Upsert sur (user_id, id_parcelle).
    Convertir geometry GeoJSON en objet PostGIS avec ST_GeomFromGeoJSON().
    Retourner l'instance Django model Parcelle créée ou mise à jour.
    """
```

---

## Tâche 4 — Service altimétrique (`ign/altimetrie.py`)

### 4a. Grille d'altitudes sur la parcelle

```python
def compute_elevation_grid(bbox: list, grid_size: int = 20) -> list[dict]:
    """
    Génère une grille NxN sur la bounding box et récupère l'altitude RGE ALTI®.

    grid_size=20 → 400 points. Bon compromis pour une parcelle standard (200-2000 m²).
    Pour parcelles > 5000 m² → utiliser grid_size=30.

    Appel IGN (POST, un seul appel pour tous les points) :
    POST https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json
    Body :
    {
        "lon": "2.347|2.350|...",   # toutes les longitudes séparées par |
        "lat": "48.859|48.859|...", # toutes les latitudes séparées par |
        "resource": "ign_rge_alti_wld",
        "delimiter": "|",
        "indent": false,
        "measures": false,
        "zonly": false
    }

    IMPORTANT : Si grid_size > 25 (> 625 points), découper en batches de
    500 points et agréger. Respecter le rate limit : 5 req/s pour l'altimétrie.

    Filtrer les points hors couverture (z == -99999).

    Retourner : [{"lon": float, "lat": float, "z": float}, ...]
    """
```

### 4b. Statistiques altimétriques

```python
def compute_altitude_stats(elevation_grid: list[dict]) -> dict:
    """
    Calcule depuis la grille :

    {
        "altitude_min":           float,  # mètres NGF
        "altitude_max":           float,
        "altitude_moyenne":       float,
        "denivele_total":         float,  # max - min
        "pente_max_degres":       float,
        "pente_moyenne_degres":   float,
        "pente_max_pourcent":     float,
        "zones_pente_forte":      list,   # points où pente > 15°
        "is_plat":                bool,   # pente_max < 3°
        "is_pentu":               bool,   # pente entre 3° et 15°
        "is_tres_pentu":          bool,   # pente > 15°
    }

    Calcul de pente entre deux points adjacents :
        delta_z   = |z2 - z1| en mètres
        distance  = haversine(lon1, lat1, lon2, lat2) en mètres
        pente_deg = atan(delta_z / distance) * (180 / pi)
    """
```

---

## Tâche 5 — Diagnostic terrassement (`ign/diagnostics.py`)

```python
def compute_earthwork_diagnostic(parcelle) -> dict:
    """
    Analyse complète du terrassement nécessaire.

    Algorithme :
    1. Charger relief_data (grille altitudes) depuis parcelle.relief_data
    2. Niveau de référence (NGF cible) = altitude_moyenne
    3. Pour chaque cellule :
       - z > niveau_ref → déblai (à excaver)
       - z < niveau_ref → remblai (à combler)
       - volume = surface_cellule_m2 * |z - niveau_ref|
    4. Agréger volumes déblai et remblai

    Retourner :
    {
        "niveau_reference_m":    float,
        "volume_deblai_m3":      float,
        "volume_remblai_m3":     float,
        "volume_net_m3":         float,   # déblai - remblai
        "terrassement_requis":   bool,    # True si volume_net > 5 m³
        "complexite":            str,     # "simple" | "moderee" | "complexe"
        "recommandations":       list[str],
        "zones_intervention":    dict,    # GeoJSON zones à traiter
        "cout_estime_eur":       dict,    # {"min": int, "max": int}
    }

    Barème de complexité :
    - simple   : pente_max < 5°  ET volume_net < 20 m³
    - moderee  : pente entre 5° et 15°  OU volume entre 20 et 100 m³
    - complexe : pente > 15°  OU volume > 100 m³

    Barème de coût indicatif :
    - Déblai  : 15-25 €/m³
    - Remblai : 20-35 €/m³
    Afficher toujours comme estimation, jamais comme devis.
    """
```

---

## Tâche 6 — Endpoints REST (`api/views/parcelle_views.py`)

### `GET /api/parcelle/autocomplete/?q=<texte>`
```
Auth : JWT requise
Action : geocodage.autocomplete_address(q)
Réponse : [{label, x, y}]
Rate limit Django : 20 req/min par utilisateur (django-ratelimit)
```

### `POST /api/parcelle/fetch/`
```
Body : {"address": "..."} OU {"lon": float, "lat": float}
Auth : JWT requise
Action :
  1. get_parcelle_from_address() ou get_parcelle_from_coords()
  2. save_parcelle_to_db(user_id, data)
  3. compute_altimetry_task.delay(parcelle.id)  # Celery async
  4. Retourner immédiatement sans attendre l'altimétrie
Réponse HTTP 201 : ParcelleSummarySerializer + "alti_status": "pending"
```

### `GET /api/parcelle/<id>/`
```
Auth : JWT + vérifier parcelle.user_id == request.user.id
Réponse : ParcelleDetailSerializer complet avec "alti_status"
```

### `GET /api/parcelle/<id>/diagnostic/`
```
Auth : JWT requise
Si alti_status != "ready" → HTTP 202 + {"status": "pending"}
Sinon → compute_earthwork_diagnostic(parcelle) → résultat complet
```

---

## Tâche 7 — Tâche Celery (`tasks/ign_tasks.py`)

```python
@shared_task(bind=True, max_retries=3)
def compute_altimetry_task(self, parcelle_id: int):
    """
    Tâche asynchrone post-création de parcelle.

    1. Charger Parcelle depuis la DB
    2. compute_elevation_grid(parcelle.bbox, grid_size=20)
    3. compute_altitude_stats(grid)
    4. Mettre à jour parcelle : relief_data, altitude_*, pente_*, alti_status="ready"
    5. En cas d'erreur IGN → self.retry(countdown=30 * (2 ** self.request.retries))
    6. Après 3 échecs → parcelle.alti_status = "error", save
    """
```

---

## Tâche 8 — Tests (`ign/tests/`)

### `test_geocodage.py`
```
- test_geocode_known_address     : "1 place du Parvis Notre-Dame 75004 Paris"
                                   → lat ≈ 48.853, lon ≈ 2.349
- test_geocode_invalid_address   : adresse vide → IGNGeocodeError
- test_geocode_low_score         : adresse ambiguë → IGNGeocodeError si score < 0.5
- test_autocomplete_returns_list : "10 rue de la P" → liste non vide
- test_reverse_geocode           : lat/lon Paris → label contient "Paris"
```

### `test_cadastre.py`
```
- test_get_parcelle_from_coords  : coordonnées Paris → id_parcelle non vide
- test_surface_positive          : surface_m2 > 0
- test_geometry_is_polygon       : geometry["type"] == "Polygon"
- test_flux_complet              : adresse complète → parcelle en une fonction
- test_not_found                 : coordonnées mer → IGNCadastreNotFoundError
```

### `test_altimetrie.py`
```
- test_elevation_single_point    : Lyon (4.83, 45.74) → z entre 150 et 250 m
- test_elevation_grid_20x20      : bbox Lyon → 400 points retournés
- test_stats_flat_terrain        : grille plateau → pente_max < 1°
- test_stats_sloped_terrain      : grille en pente artificielle → pente détectée
- test_batch_split_large_grid    : grid_size=30 (900 pts) → ≤ 2 appels HTTP IGN
```

### `test_diagnostics.py`
```
- test_terrain_plat              : pente < 3° → complexite="simple",
                                   terrassement_requis=False
- test_terrain_pentu             : pente > 15° → complexite="complexe"
- test_volumes_calcul            : grille connue → volumes corrects
- test_cout_range                : cout_min < cout_max, tous deux > 0
```

---

## Tâche 9 — Modèle Django et migration

Dans `parcelles/models.py` :
```python
from django.contrib.gis.db import models as gis_models

class Parcelle(models.Model):
    # Utiliser gis_models.PolygonField(srid=4326) pour le champ geom
    # Tous les champs du schéma SQL ci-dessus
    # Propriété @property alti_status dérivée du champ alti_status VARCHAR

    class Meta:
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["code_insee"]),
        ]
```

S'assurer que `django.contrib.gis` est dans `INSTALLED_APPS` et que
PostGIS est activé : `CREATE EXTENSION IF NOT EXISTS postgis;`

---

## Exemple de réponse complète (GET /api/parcelle/42/diagnostic/)

```json
{
  "parcelle_id": 42,
  "surface_m2": 412.50,
  "niveau_reference_m": 186.4,
  "altitude_min": 183.1,
  "altitude_max": 191.2,
  "denivele_total": 8.1,
  "pente_max_degres": 12.3,
  "pente_moyenne_degres": 5.8,
  "terrassement_requis": true,
  "complexite": "moderee",
  "volume_deblai_m3": 34.2,
  "volume_remblai_m3": 8.7,
  "volume_net_m3": 25.5,
  "cout_estime_eur": { "min": 1200, "max": 2400 },
  "recommandations": [
    "Un terrassement modéré est nécessaire sur la partie nord de la parcelle.",
    "Prévoir l'évacuation d'environ 25 m³ de terre.",
    "Consulter un terrassier pour affiner le devis."
  ],
  "is_plat": false,
  "is_pentu": true,
  "is_tres_pentu": false
}
```

---

## Notes importantes

- **PostGIS obligatoire** : toujours utiliser les types PostGIS (`PolygonField`,
  `PointField`) — ne jamais stocker du GeoJSON brut en TEXT.

- **Parcellaire Express (PCI) uniquement** : ne pas utiliser la BD Parcellaire
  (arrêtée depuis 2018). Le module cadastre d'API Carto utilise PCI par défaut.

- **Calcul altimétrique asynchrone obligatoire** : le calcul d'une grille 20x20
  prend 2-5s. Toujours passer par Celery, ne jamais bloquer la réponse HTTP.

- **Grandes parcelles** : si surface > 50 000 m², avertir l'utilisateur que la
  parcelle semble atypique (voirie, espace public). Ajouter une validation.

- **Précision altimétrique** : RGE ALTI® = résolution 1m urbain, 5m rural.
  Toujours afficher cette limite dans l'interface utilisateur pour les diagnostics.

- **Coûts = estimatifs uniquement** : ne jamais présenter les fourchettes de coût
  comme des devis. Toujours accompagner d'un disclaimer "estimation indicative".