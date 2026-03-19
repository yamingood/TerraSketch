# TerraSketch — Script d'enrichissement de la base de plantes

## Contexte

Ce script enrichit la table `plants` de TerraSketch (PostgreSQL + PostGIS) en
interrogeant deux APIs botaniques gratuites :

- **Trefle.io** — données culturales (température min/max, pH, profondeur racines,
  lumière, arrosage)
- **GBIF** — validation des zones climatiques et répartition géographique en France

La base de données source est `terrasketch_plants_database.json` (160 plantes).

---

## Objectif

Pour chaque plante du fichier JSON :

1. Rechercher la correspondance dans Trefle via `name_latin`
2. Récupérer les champs manquants : `min_temp`, `max_temp`, `ph_minimum`,
   `ph_maximum`, `root_depth_minimum_cm`, `growth_rate`, `toxicity`,
   `image_url` (première image libre de droits depuis Trefle)
3. Valider / corriger les `climate_zones` via GBIF occurrences France
4. Insérer ou mettre à jour (`upsert`) chaque plante dans PostgreSQL
5. Logger les plantes non trouvées dans `enrichment_errors.json`

---

## Stack technique

- **Backend** : Django + psycopg2
- **Base de données** : PostgreSQL avec PostGIS
- **Langage** : Python 3.11+
- **APIs** : Trefle.io (token requis), GBIF (pas d'auth requise)

---

## Variables d'environnement requises

```
DATABASE_URL=postgresql://user:password@localhost:5432/terrasketch
TREFLE_API_TOKEN=your_trefle_token_here
```

Créer un compte gratuit sur https://trefle.io pour obtenir le token.

---

## Structure de la table PostgreSQL cible

Créer (ou altérer) la table `plants` avec ce schéma :

```sql
CREATE TABLE IF NOT EXISTS plants (
    id                      SERIAL PRIMARY KEY,
    name_latin              VARCHAR(255) UNIQUE NOT NULL,
    name_common             VARCHAR(255),
    description             TEXT,
    family                  VARCHAR(100),
    category                VARCHAR(50),
    styles                  TEXT[],                  -- ex: ['Contemporain', 'Japonais']
    size_adult_height       DECIMAL(5,2),            -- mètres
    size_adult_width        DECIMAL(5,2),            -- mètres
    sun_requirements        VARCHAR(20),             -- full_sun | partial_shade | shade
    watering_needs          VARCHAR(20),             -- low | moderate | high
    hardiness_zone          VARCHAR(10),             -- ex: Z6
    bloom_season            VARCHAR(20),             -- printemps | été | automne | hiver
    root_type               VARCHAR(20),             -- invasive | non_invasive
    climate_zones           TEXT[],                  -- ['Atlantique', 'Continental', ...]

    -- Champs enrichis par Trefle
    trefle_id               INTEGER,
    min_temp_celsius         DECIMAL(5,1),
    max_temp_celsius         DECIMAL(5,1),
    ph_minimum              DECIMAL(4,2),
    ph_maximum              DECIMAL(4,2),
    root_depth_minimum_cm   INTEGER,
    growth_rate             VARCHAR(20),             -- slow | moderate | fast
    toxicity                VARCHAR(50),
    image_url               TEXT,

    -- Métadonnées
    trefle_enriched_at      TIMESTAMP,
    gbif_validated_at       TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);
```

---

## Tâches à implémenter

### Tâche 1 — Script principal `enrich_plants.py`

Créer `scripts/enrich_plants.py` avec la logique suivante :

```
1. Charger terrasketch_plants_database.json
2. Pour chaque plante dans plants[]:
   a. Appeler GET https://trefle.io/api/v1/plants/search?q={name_latin}&token={TOKEN}
   b. Si résultat trouvé, extraire les champs Trefle utiles
   c. Appeler GET https://api.gbif.org/v1/occurrence/search?scientificName={name_latin}&country=FR&limit=1
   d. Depuis les résultats GBIF, déduire les zones climatiques françaises
      en mappant les coordonnées GPS sur les zones (voir mapping ci-dessous)
   e. Upsert dans PostgreSQL avec ON CONFLICT (name_latin) DO UPDATE
   f. En cas d'échec, logger dans enrichment_errors.json
3. Afficher un résumé : X plantes enrichies, Y erreurs
```

### Tâche 2 — Mapping coordonnées GPS → zones climatiques

Implémenter la fonction `coords_to_climate_zone(lat, lon)` :

```
Atlantique  : lon < 2.5 et lat entre 43 et 51 (façade ouest)
Méditerranéen : lat < 44.5 et lon > 3 (sud-est)
Continental : lon > 2.5 et lat entre 44 et 50 (intérieur)
Montagnard  : zones Alpes (lat 44-46, lon 5.5-7.5) et
              Pyrénées (lat 42.5-43.5, lon -2 à 3) et
              Massif Central (lat 44-46, lon 2-4)
```

### Tâche 3 — Mapping champs Trefle → modèle TerraSketch

```python
TREFLE_FIELD_MAP = {
    "minimum_temperature.deg_c": "min_temp_celsius",
    "maximum_temperature.deg_c": "max_temp_celsius",
    "soil_nutriments":          None,  # ignorer
    "ph_minimum":               "ph_minimum",
    "ph_maximum":               "ph_maximum",
    "minimum_root_depth":       "root_depth_minimum_cm",  # en cm
    "growth_rate":              "growth_rate",
    "toxicity":                 "toxicity",
    # image : prendre image_url dans data[0].image_url
}
```

**Mapping `sun_requirements` Trefle → TerraSketch :**

```
"Full Sun"     → "full_sun"
"Part Shade"   → "partial_shade"
"Full Shade"   → "shade"
```

**Mapping `watering_needs` Trefle → TerraSketch :**

```
light      → "low"
average    → "moderate"
frequent   → "high"
```

### Tâche 4 — Gestion des erreurs et rate limiting

- Respecter le rate limit Trefle : **120 req/min** → ajouter `time.sleep(0.5)` entre chaque appel
- Retry automatique (3 tentatives) sur erreurs HTTP 429 et 503
- Logger dans `enrichment_errors.json` :
  ```json
  [
    {
      "name_latin": "Plante inconnue",
      "error": "Trefle: not found",
      "timestamp": "2025-01-01T12:00:00"
    }
  ]
  ```

### Tâche 5 — Commande Django de management

Wrapper le script comme commande Django :

```
python manage.py enrich_plants [--dry-run] [--limit N] [--only-missing]
```

Options :
- `--dry-run` : afficher les enrichissements sans écrire en base
- `--limit N` : traiter seulement N plantes (pour tester)
- `--only-missing` : ne traiter que les plantes sans `trefle_id`

---

## Fichiers à créer

```
scripts/
  enrich_plants.py          # logique principale (standalone)
plants/
  management/
    commands/
      enrich_plants.py      # wrapper commande Django
  migrations/
    XXXX_add_enrichment_fields.py   # migration ALTER TABLE
```

---

## Tests à écrire

Créer `plants/tests/test_enrichment.py` avec :

1. `test_trefle_search_found` — mock HTTP 200, vérifier mapping des champs
2. `test_trefle_search_not_found` — mock HTTP 200 résultat vide, vérifier log erreur
3. `test_gbif_climate_zone_mapping` — tester `coords_to_climate_zone()` avec
   coordonnées connues (Paris → Continental, Marseille → Méditerranéen, etc.)
4. `test_upsert_plant` — vérifier qu'un doublon `name_latin` met à jour sans créer
5. `test_rate_limit_retry` — mock HTTP 429, vérifier 3 tentatives puis log erreur

---

## Exemple de sortie attendue

```
🌿 TerraSketch — Enrichissement de la base de plantes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chargement de terrasketch_plants_database.json... 160 plantes
Connexion PostgreSQL... OK
Connexion Trefle API... OK

[  1/160] Lavandula angustifolia     ✅ Trefle #131026  ✅ GBIF validé
[  2/160] Buxus sempervirens         ✅ Trefle #134521  ⚠️  GBIF: aucune occurrence FR
[  3/160] Acer palmatum              ✅ Trefle #89234   ✅ GBIF validé
[  4/160] Plante inexistante xyz     ❌ Trefle: not found
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Enrichies avec succès : 147 / 160
⚠️  GBIF non validé       :   8 / 160
❌ Non trouvées (Trefle)  :   5 / 160
📄 Erreurs loguées dans enrichment_errors.json
⏱  Durée totale : 2m 34s
```

---

## Notes importantes

- La colonne `name_latin` est la clé de correspondance principale avec Trefle.
  Si le nom exact ne match pas, essayer avec seulement le genre + espèce
  (sans le cultivar entre guillemets). Ex: `Photinia x fraseri 'Red Robin'`
  → essayer d'abord `Photinia x fraseri`, puis `Photinia fraseri`.

- Les images Trefle sont sous licence CC-BY-SA. Les stocker dans Cloudflare R2
  avec attribution, pas en direct linking.

- Ne pas écraser les champs déjà renseignés dans la base si Trefle renvoie NULL.
  Toujours faire un merge : `UPDATE SET field = COALESCE(trefle_value, existing_value)`.