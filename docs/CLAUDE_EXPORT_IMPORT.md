# TerraSketch — Module Export/Import Projets (.tsk)

## Contexte

Ce module gère l'export d'un projet TerraSketch au format `.tsk` et son
import ultérieur, que ce soit par le même utilisateur ou par un autre
paysagiste pro TerraSketch.

Le format `.tsk` est un ZIP structuré contenant les données JSON du projet
et ses assets textuels (pas de rendus 3D — ceux-ci sont régénérés à l'import).

Les exports additionnels PDF, DXF et CSV sont également gérés dans ce module.

---

## Choix architecturaux validés

| Paramètre               | Décision                                              |
|------------------------|-------------------------------------------------------|
| Format .tsk            | ZIP structuré (JSON + assets textuels)                |
| Rendus 3D              | Exclus — régénérés à l'import                         |
| Rétrocompatibilité     | Obligatoire — toutes versions futures lisent v1+      |
| Partage inter-pros     | Oui — projet entièrement transférable                 |
| Devis dans le .tsk     | Optionnel — choix du pro à l'export                   |
| Exports additionnels   | PDF rapport complet, DXF, CSV plantes + quantités     |

---

## Structure du fichier .tsk

Un `.tsk` est un fichier ZIP renommé. Son contenu interne :

```
projet_nom_client_2025-03-17.tsk  (ZIP)
├── manifest.json          ← métadonnées + version + checksum
├── project.json           ← données complètes du projet
├── parcelle.geojson       ← géométrie WGS84 de la parcelle
├── topographie.json       ← grille altimétrique + diagnostics terrain
└── assets/
    └── cadastre_original/ ← fichier cadastral déposé par l'utilisateur (optionnel)
        └── source.{ext}   ← .geojson | .dxf | .shp | etc.
```

### `manifest.json`

```json
{
  "tsk_version": "1.0",
  "terrasketch_version": "1.2.0",
  "created_at": "2025-03-17T14:32:00Z",
  "exported_at": "2025-03-17T14:32:00Z",
  "exported_by": {
    "pro_id": 42,
    "name": "Jean Dupont Paysages",
    "email": "jean@dupont-paysages.fr"
  },
  "project_id": "proj_8f3a2c1d",
  "project_name": "Jardin Famille Martin - Bordeaux",
  "includes_quote": false,
  "checksums": {
    "project.json": "sha256:abc123...",
    "parcelle.geojson": "sha256:def456...",
    "topographie.json": "sha256:ghi789..."
  }
}
```

### `project.json`

```json
{
  "schema_version": "1.0",
  "project": {
    "id": "proj_8f3a2c1d",
    "name": "Jardin Famille Martin - Bordeaux",
    "created_at": "2025-03-01T10:00:00Z",
    "updated_at": "2025-03-17T14:30:00Z",
    "status": "completed"
  },
  "client": {
    "name": "Famille Martin",
    "city": "Bordeaux",
    "note": "Préfère les plantes méditerranéennes"
  },
  "parcelle": {
    "id_parcelle": "330630000AB0042",
    "surface_m2": 450.0,
    "surface_ha": 0.045,
    "nom_commune": "Bordeaux",
    "code_insee": "33063",
    "adresse_normalisee": "12 rue des Acacias, 33000 Bordeaux",
    "longitude": -0.5792,
    "latitude": 44.8378
  },
  "preferences": {
    "style_jardin": "mediterraneen",
    "ambiance": ["zen", "coloré"],
    "usages": ["détente", "potager"],
    "budget_total": 12000,
    "phases": 2,
    "niveau_entretien": "faible",
    "enfants": false,
    "animaux": ["chien"],
    "plantes_exclues": [],
    "plantes_souhaitees": ["Lavande", "Rosier"],
    "fruitiers_souhaites": true
  },
  "plan": {
    "resume": "Un jardin méditerranéen...",
    "zones": [...],
    "plantes": [...],
    "cheminements": [...],
    "terrassement": {...},
    "budget": {...},
    "calendrier_entretien": {...},
    "simulation_temporelle": {...},
    "conseils_specifiques": [...]
  },
  "quote": null,
  "generated_at": "2025-03-01T10:05:00Z",
  "ai_model_used": "claude-opus-4-5"
}
```

Si `includes_quote: true` dans le manifest, le champ `quote` contient :

```json
"quote": {
  "lignes_plantes": [...],
  "lignes_materiaux": [...],
  "sous_total_ht": 9500.00,
  "total_tva": 1050.00,
  "total_ttc": 10550.00,
  "phases": [...],
  "snapshot_date": "2025-03-17",
  "currency": "EUR"
}
```

---

## Stratégie de rétrocompatibilité

Le champ `schema_version` dans `project.json` permet de gérer les migrations.

### Règles immuables

1. **Jamais supprimer un champ** — le rendre nullable si obsolète
2. **Toujours ajouter, jamais renommer** — nouveau champ = nouvelle clé
3. **Migration automatique à l'import** — `MigrationEngine` convertit v1→v2→v3
4. **Champ `_deprecated`** — préfixe pour signaler les champs obsolètes à terme

### Migration engine

```python
MIGRATIONS = {
    "1.0": lambda data: data,           # version de base, no-op
    "1.1": migrate_v1_0_to_v1_1,       # ex: renommage d'un sous-champ
    "1.2": migrate_v1_1_to_v1_2,       # ex: ajout d'un champ obligatoire
}

def migrate_to_latest(data: dict) -> dict:
    """
    Applique en cascade toutes les migrations depuis la version du fichier
    jusqu'à la version courante de TerraSketch.
    """
    version = data.get("schema_version", "1.0")
    versions = list(MIGRATIONS.keys())
    start_idx = versions.index(version)
    for v in versions[start_idx + 1:]:
        data = MIGRATIONS[v](data)
        data["schema_version"] = v
    return data
```

---

## Stack technique

- **Backend** : Django + Django REST Framework
- **ZIP** : zipfile (stdlib Python)
- **Checksums** : hashlib (stdlib)
- **PDF** : WeasyPrint ou ReportLab
- **DXF** : ezdxf (déjà dans les dépendances)
- **CSV** : csv (stdlib)
- **Validation JSON** : jsonschema

---

## Dépendances à ajouter dans requirements.txt

```
jsonschema>=4.21.0     # validation schéma project.json à l'import
weasyprint>=60.0       # génération PDF (ou reportlab>=4.0 selon préférence)
```

---

## Schéma PostgreSQL

```sql
-- Registre des exports effectués (traçabilité)
CREATE TABLE IF NOT EXISTS project_exports (
    id              SERIAL PRIMARY KEY,
    project_id      VARCHAR(50) NOT NULL,
    exported_by     INTEGER REFERENCES users(id),
    export_format   VARCHAR(20) NOT NULL,
    -- 'tsk' | 'pdf' | 'dxf' | 'csv'
    includes_quote  BOOLEAN DEFAULT FALSE,
    file_size_bytes INTEGER,
    r2_key          VARCHAR(500),   -- clé Cloudflare R2 si stocké
    expires_at      TIMESTAMP,      -- lien de téléchargement temporaire
    downloaded_at   TIMESTAMP,      -- NULL si jamais téléchargé
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Registre des imports effectués (traçabilité + audit)
CREATE TABLE IF NOT EXISTS project_imports (
    id              SERIAL PRIMARY KEY,
    imported_by     INTEGER REFERENCES users(id),
    source_pro_id   INTEGER,        -- pro d'origine (depuis manifest)
    source_pro_name VARCHAR(255),
    tsk_version     VARCHAR(10),
    schema_version  VARCHAR(10),
    migrations_applied  TEXT[],     -- liste des migrations appliquées
    new_project_id  VARCHAR(50),    -- ID du projet créé à l'import
    included_quote  BOOLEAN,
    quote_imported  BOOLEAN,        -- FALSE si refusé à l'import
    warnings        JSONB,          -- avertissements non bloquants
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## Structure des fichiers à créer

```
exports/
  __init__.py
  models.py                  # ProjectExport, ProjectImport
  views.py                   # Endpoints API export/import
  urls.py
  serializers.py
  permissions.py             # IsProjectOwner
  services/
    __init__.py
    tsk_exporter.py          # Génération .tsk
    tsk_importer.py          # Lecture + validation + import .tsk
    tsk_migrator.py          # Migrations de versions
    tsk_validator.py         # Validation schéma JSON
    pdf_exporter.py          # Export PDF rapport complet
    dxf_exporter.py          # Export DXF
    csv_exporter.py          # Export CSV plantes + quantités
  schemas/
    project_v1.0.json        # JSON Schema de référence v1.0
  tests/
    __init__.py
    test_tsk_exporter.py
    test_tsk_importer.py
    test_tsk_migrator.py
    test_pdf_exporter.py
    test_dxf_exporter.py
    test_csv_exporter.py
    test_views.py
  migrations/
    0001_initial.py
```

---

## Tâche 1 — Exporteur .tsk `exports/services/tsk_exporter.py`

```python
def export_project_to_tsk(
    project_id: str,
    exported_by_user_id: int,
    include_quote: bool = False,
    include_cadastre_source: bool = True,
) -> bytes:
    """
    Génère le fichier .tsk en mémoire et retourne ses bytes.

    Étapes :
    1. Charger le projet depuis PostgreSQL (project + parcelle + topographie)
    2. Construire project.json selon le schéma défini
    3. Construire manifest.json avec checksums SHA-256
    4. Si include_quote=True : inclure les données de devis dans project.json
       Si False : champ quote=null
    5. Si include_cadastre_source=True et fichier source disponible :
       inclure dans assets/cadastre_original/
    6. Assembler le ZIP en mémoire (io.BytesIO)
    7. Logger dans project_exports
    8. Retourner bytes du ZIP

    Nommage du fichier suggéré retourné dans les headers HTTP :
    terrasketch_{slug_projet}_{YYYY-MM-DD}.tsk
    """


def build_project_json(project_id: str, include_quote: bool) -> dict:
    """
    Construit le dict project.json depuis les modèles Django.
    Respecter strictement le schéma défini dans schemas/project_v1.0.json.

    Données à inclure :
    - project metadata
    - client info (anonymisé si partagé avec autre pro : nom uniquement)
    - parcelle (toutes les données cadastrales)
    - preferences utilisateur
    - plan complet (zones, plantes, cheminements, terrassement,
      budget, calendrier, simulation temporelle)
    - quote si include_quote=True, null sinon
    - generated_at, ai_model_used
    """


def compute_checksums(files: dict) -> dict:
    """
    Calcule les checksums SHA-256 de chaque fichier du ZIP.
    files = {"project.json": bytes, "parcelle.geojson": bytes, ...}
    Retourne : {"project.json": "sha256:abc...", ...}
    """
```

---

## Tâche 2 — Importeur .tsk `exports/services/tsk_importer.py`

```python
def import_tsk_file(
    file_bytes: bytes,
    imported_by_user_id: int,
    import_quote: bool = True,
) -> dict:
    """
    Importe un fichier .tsk et crée un nouveau projet dans TerraSketch.

    Étapes :
    1. Décompresser le ZIP en mémoire
    2. Vérifier présence de manifest.json et project.json
    3. Valider les checksums SHA-256
    4. Lire manifest.json → tsk_version, schema_version, source pro
    5. Valider project.json contre le JSON Schema (jsonschema)
    6. Appeler migrate_to_latest() si schema_version < version courante
    7. Créer un nouveau projet (nouvel ID, timestamp import)
    8. Importer parcelle → upsert dans table parcelles
    9. Importer topographie
    10. Importer plan
    11. Si import_quote=True et quote présente → importer devis
        Si import_quote=False → ignorer le devis
    12. Importer assets/cadastre_original/ si présent (vers R2)
    13. Logger dans project_imports avec migrations_applied et warnings
    14. Retourner le nouveau projet créé

    Gestion des avertissements non bloquants :
    - Plante dans le plan inconnue de la DB locale → warning, pas d'erreur
    - Prix du devis déphasés (plantes supprimées du catalogue) → warning
    - Migrations appliquées → listed dans warnings pour info

    Lève :
    - TSKChecksumError    → fichier corrompu
    - TSKSchemaError      → project.json invalide et non migrable
    - TSKVersionError     → tsk_version non supportée
    """


def validate_checksums(zip_file, manifest: dict) -> None:
    """
    Vérifie l'intégrité de chaque fichier listé dans manifest.checksums.
    Lève TSKChecksumError si un checksum ne correspond pas.
    """


def create_project_from_import(
    project_data: dict,
    imported_by_user_id: int,
    import_quote: bool,
) -> Project:
    """
    Crée le projet Django depuis le dict project.json migré.
    Génère un nouvel ID projet (ne pas réutiliser l'ID source).
    Marque le projet avec source="tsk_import" et source_pro dans les métadonnées.
    """
```

---

## Tâche 3 — Migrateur `exports/services/tsk_migrator.py`

```python
CURRENT_SCHEMA_VERSION = "1.0"

MIGRATIONS = {
    "1.0": lambda data: data,  # no-op, version initiale
    # Futures migrations ajoutées ici :
    # "1.1": migrate_v1_0_to_v1_1,
}

def migrate_to_latest(data: dict) -> tuple[dict, list[str]]:
    """
    Migre project.json de sa version vers CURRENT_SCHEMA_VERSION.
    Retourne (data_migrée, liste_migrations_appliquées).

    Si la version est inconnue (plus récente que le code) :
    Tenter l'import en mode dégradé avec les champs connus.
    Logger un warning 'version_future_detected'.
    """


def migrate_v1_0_to_v1_1(data: dict) -> dict:
    """
    Exemple de migration future — à implémenter quand nécessaire.
    Toujours : ajouter les nouveaux champs avec valeurs par défaut,
    ne jamais supprimer de champs.
    """
```

---

## Tâche 4 — Validateur `exports/services/tsk_validator.py`

```python
def validate_project_json(data: dict) -> list[str]:
    """
    Valide project.json contre le JSON Schema dans schemas/project_v1.0.json.
    Retourne la liste des erreurs de validation (vide si valide).
    Utilise jsonschema.validate().
    """


def validate_tsk_zip_structure(zip_file) -> None:
    """
    Vérifie que le ZIP contient les fichiers obligatoires :
    - manifest.json
    - project.json
    - parcelle.geojson
    - topographie.json
    Lève TSKStructureError si un fichier manque.
    """
```

Créer `exports/schemas/project_v1.0.json` — le JSON Schema complet
correspondant à la structure de `project.json` définie dans ce fichier.
Tous les champs obligatoires doivent être marqués `"required"`.
Les champs optionnels (comme `quote`) peuvent être `null`.

---

## Tâche 5 — Export PDF `exports/services/pdf_exporter.py`

```python
def export_project_to_pdf(
    project_id: str,
    include_quote: bool = True,
    include_plant_list: bool = True,
    include_maintenance_calendar: bool = True,
) -> bytes:
    """
    Génère un rapport PDF complet du projet.

    Structure du PDF :
    Page de garde
      - Logo TerraSketch / Polsia
      - Nom du projet + client
      - Nom du paysagiste pro
      - Date de génération

    Section 1 — Présentation du terrain
      - Adresse + commune
      - Surface + orientations
      - Diagnostics terrassement (complexité, dénivelé)
      - Carte de la parcelle (image PNG depuis le GeoJSON via staticmap ou équivalent)

    Section 2 — Le projet
      - Résumé du plan (champ resume)
      - Plan de masse schématique (représentation 2D des zones)
      - Description de chaque zone

    Section 3 — Liste des plantes
      Si include_plant_list=True :
      Tableau : Nom commun | Nom latin | Quantité | Taille | Zone | Floraison
      Groupé par zone

    Section 4 — Devis estimatif
      Si include_quote=True :
      Tableau plantes HT + TVA + TTC
      Tableau matériaux HT + TVA + TTC
      Récapitulatif par phase
      Total général TTC

    Section 5 — Planning des travaux
      Timeline visuelle des phases

    Section 6 — Calendrier d'entretien
      Si include_maintenance_calendar=True :
      Tableau 12 mois × tâches

    Pied de page sur chaque page :
      Logo + numéro de page + "Généré par TerraSketch - Polsia"

    Utiliser WeasyPrint avec un template HTML/CSS dédié.
    Template : exports/templates/pdf/rapport_projet.html
    """
```

Créer `exports/templates/pdf/rapport_projet.html` — template HTML/CSS
pour WeasyPrint. Utiliser la palette de couleurs TerraSketch (vert #2D6A4F).
Mise en page A4, marges 20mm, police sans-serif professionnelle.

---

## Tâche 6 — Export DXF `exports/services/dxf_exporter.py`

```python
def export_project_to_dxf(project_id: str) -> bytes:
    """
    Génère un fichier DXF compatible AutoCAD/ArchiCAD via ezdxf.

    Projection : Lambert 93 (EPSG:2154) — standard CAO France.
    Reprojeter la géométrie WGS84 → Lambert93 via pyproj avant export.

    Layers DXF à créer :
    - "PARCELLE"         → polygone de la parcelle (couleur rouge, lw=0.5)
    - "ZONE_TERRASSE"    → polygones zones terrasse (couleur grise)
    - "ZONE_PELOUSE"     → polygones zones pelouse (couleur verte)
    - "ZONE_MASSIF"      → polygones zones massifs (couleur marron)
    - "ZONE_POTAGER"     → polygones zones potager
    - "ZONE_ALLEE"       → polygones allées
    - "ZONE_EAU"         → polygones zones eau
    - "PLANTES"          → cercles représentant chaque plante
                           rayon = size_adult_width / 2
                           ATTRIB avec name_common + quantite
    - "CHEMINEMENTS"     → polylignes des cheminements
    - "COTES"            → cotations de surface (optionnel)
    - "TEXTES"           → annotations des zones

    Conversion positions du plan (x_pct, y_pct) → coordonnées Lambert93 :
    Utiliser la bbox de la parcelle comme référentiel.

    Métadonnées DXF (en-tête) :
    - Titre : nom du projet
    - Auteur : nom du paysagiste
    - Date : date d'export
    - Unités : mètres

    Retourne les bytes du fichier .dxf.
    """
```

---

## Tâche 7 — Export CSV `exports/services/csv_exporter.py`

```python
def export_plants_to_csv(project_id: str, include_prices: bool = False) -> str:
    """
    Génère un CSV de toutes les plantes du projet.

    Colonnes :
    nom_commun, nom_latin, famille, categorie, quantite, taille_recommandee,
    zone, position_dans_zone, floraison, besoins_soleil, besoins_eau,
    hauteur_adulte_m, largeur_adulte_m, zone_rusticite, justification

    Si include_prices=True (pro uniquement) :
    + prix_unitaire_ht, tva_pct, prix_unitaire_ttc, prix_total_ttc

    Encodage : UTF-8 avec BOM (pour compatibilité Excel français)
    Séparateur : point-virgule (standard FR)
    Retourne le contenu CSV (string).
    """
```

---

## Tâche 8 — Endpoints DRF `exports/views.py`

```
POST   /api/projects/{project_id}/export/tsk/
       Body : {include_quote: bool, include_cadastre_source: bool}
       Réponse : fichier .tsk en téléchargement direct
       Content-Type: application/zip
       Content-Disposition: attachment; filename="terrasketch_....tsk"
       Permission : IsProjectOwner

POST   /api/projects/{project_id}/export/pdf/
       Body : {include_quote: bool, include_plant_list: bool,
               include_maintenance_calendar: bool}
       Réponse : fichier .pdf en téléchargement
       Permission : IsProjectOwner

POST   /api/projects/{project_id}/export/dxf/
       Réponse : fichier .dxf en téléchargement
       Permission : IsProjectOwner (pro uniquement)

POST   /api/projects/{project_id}/export/csv/
       Body : {include_prices: bool}
       Réponse : fichier .csv en téléchargement
       Permission : IsProjectOwner

POST   /api/projects/import/tsk/
       Body : multipart, champ "tsk_file" + "import_quote": bool
       Réponse :
       {
           "new_project_id": str,
           "project_name": str,
           "source_pro": str,
           "migrations_applied": [str],
           "warnings": [...],
           "quote_imported": bool
       }
       Permission : IsProVerified
       Limite taille : 20 Mo (un .tsk sans rendus reste léger)

GET    /api/projects/{project_id}/exports/history/
       Liste les exports précédents du projet (format, date, taille).
       Permission : IsProjectOwner
```

---

## Tâche 9 — Exceptions `exports/exceptions.py`

```python
class TSKError(Exception):
    """Base"""

class TSKStructureError(TSKError):
    """Fichiers obligatoires manquants dans le ZIP"""

class TSKChecksumError(TSKError):
    """Checksum SHA-256 invalide — fichier corrompu"""

class TSKSchemaError(TSKError):
    """project.json ne respecte pas le JSON Schema"""

class TSKVersionError(TSKError):
    """Version tsk_version non supportée"""

class TSKMigrationError(TSKError):
    """Échec d'une migration de version"""

class ExportError(Exception):
    """Erreur générique lors de la génération d'un export"""

class PDFExportError(ExportError):
    """Erreur WeasyPrint"""

class DXFExportError(ExportError):
    """Erreur ezdxf"""
```

---

## Tâche 10 — Tests

### `test_tsk_exporter.py`

```
test_export_creates_valid_zip
  → Exporter un projet → vérifier que le résultat est un ZIP valide

test_export_zip_contains_required_files
  → Vérifier présence manifest.json, project.json, parcelle.geojson, topographie.json

test_export_checksums_are_correct
  → Calculer les checksums manuellement → comparer avec manifest.json

test_export_without_quote
  → include_quote=False → project.json contient quote=null

test_export_with_quote
  → include_quote=True → project.json contient les données de devis

test_export_schema_version_is_current
  → Vérifier schema_version == CURRENT_SCHEMA_VERSION dans project.json
```

### `test_tsk_importer.py`

```
test_import_valid_tsk_creates_project
  → Importer un .tsk valide → nouveau projet créé en base

test_import_generates_new_project_id
  → L'ID du projet importé ≠ l'ID source

test_import_corrupted_checksum_raises_error
  → Modifier un byte dans project.json → TSKChecksumError

test_import_missing_manifest_raises_error
  → ZIP sans manifest.json → TSKStructureError

test_import_invalid_schema_raises_error
  → project.json avec champs manquants → TSKSchemaError

test_import_with_quote_accepted
  → import_quote=True → devis présent dans le projet importé

test_import_with_quote_rejected
  → import_quote=False → devis ignoré, projet importé sans devis

test_import_unknown_plant_creates_warning
  → Plante dans le plan inconnue de la DB → warning dans project_imports

test_import_logs_to_project_imports_table
  → Vérifier entrée dans project_imports après import réussi
```

### `test_tsk_migrator.py`

```
test_migrate_current_version_is_noop
  → Fichier déjà en version courante → aucune migration appliquée

test_migrate_future_version_returns_warning
  → schema_version > CURRENT_SCHEMA_VERSION → import dégradé + warning

test_migrate_chain_applies_all_steps
  → Fichier v1.0 avec migrations v1.1 et v1.2 définies
  → Vérifier application séquentielle des deux migrations
```

### `test_csv_exporter.py`

```
test_csv_has_correct_columns
test_csv_encoding_is_utf8_bom
test_csv_separator_is_semicolon
test_csv_with_prices_included
test_csv_without_prices_excluded
```

### `test_views.py` (APITestCase)

```
test_export_tsk_returns_zip_file
test_export_tsk_unauthorized_403
test_export_tsk_wrong_owner_403
test_export_pdf_returns_pdf_file
test_export_dxf_returns_dxf_file
test_export_csv_returns_csv_file
test_import_tsk_valid_file_returns_201
test_import_tsk_too_large_returns_400
test_import_tsk_corrupted_returns_400
test_import_history_returns_list
```

---

## Tâche 11 — Composant React frontend

### Boutons d'export dans l'interface projet

Créer `frontend/src/components/project/ExportMenu.jsx` :

```
ExportMenu (dropdown bouton "Exporter")
├── "Télécharger .tsk"
│   └── Modal options :
│       ├── Toggle "Inclure le devis" (avec avertissement données sensibles)
│       ├── Toggle "Inclure le fichier cadastral source"
│       └── Bouton "Télécharger"
│
├── "Rapport PDF"
│   └── Modal options :
│       ├── Toggle "Inclure le devis estimatif"
│       ├── Toggle "Liste des plantes"
│       ├── Toggle "Calendrier d'entretien"
│       └── Bouton "Générer le PDF"
│
├── "Export DXF" (pro uniquement)
│   └── Téléchargement direct sans options
│
└── "Liste des plantes (CSV)"
    └── Modal options :
        ├── Toggle "Inclure les prix" (pro uniquement)
        └── Bouton "Télécharger"
```

### Bouton d'import

Créer `frontend/src/components/project/ImportTSK.jsx` :

```
ImportTSK
├── Zone drag & drop ou bouton "Parcourir"
├── Validation côté client : extension .tsk et taille < 20 Mo
├── Toggle "Importer aussi le devis" (si devis présent dans le fichier)
├── États :
│   ├── Idle → zone de drop
│   ├── Uploading → spinner "Analyse du fichier..."
│   ├── Migrating → "Migration du format..." (si migrations nécessaires)
│   ├── Success → "Projet importé ! [Ouvrir le projet]"
│   │   + affichage des warnings non bloquants si présents
│   └── Error → message d'erreur lisible selon le type :
│       TSKChecksumError   → "Le fichier semble corrompu. Demandez un nouvel export."
│       TSKSchemaError     → "Format de fichier non reconnu."
│       TSKVersionError    → "Cette version de .tsk n'est pas supportée."
└── Props : onImportSuccess={(project) => void}
```

---

## Tâche 12 — Migration Django

Créer `exports/migrations/0001_initial.py` pour les tables
`project_exports` et `project_imports`.

---

## Notes importantes

### Sécurité à l'import inter-pros

Quand un pro importe le `.tsk` d'un autre pro :
- Le projet importé appartient au **pro importateur** (nouvel owner)
- L'ID source et le nom du pro d'origine sont conservés dans les métadonnées
  pour traçabilité uniquement
- Si `include_quote=True` à l'export : les prix snapshot sont transférés
  mais ils référencent les tarifs du pro **exportateur**, pas de l'importateur
  → Afficher un avertissement : "Les prix de ce devis sont ceux de [Pro Dupont].
    Régénérez le devis avec vos propres tarifs."

### Taille des fichiers .tsk

Sans rendus 3D, un `.tsk` reste très léger :
- `project.json` : ~50-200 Ko selon la complexité du plan
- `parcelle.geojson` : ~5-20 Ko
- `topographie.json` : ~10-50 Ko (grille 10×10 = 100 points)
- Fichier cadastral source : 0-2 Mo selon le format
- **Total estimé : 100 Ko à 3 Mo**

La limite d'upload de 20 Mo laisse une large marge.

### Génération DXF et positions

Le plan IA stocke les positions des zones en pourcentage de la bbox parcelle
(`x_pct`, `y_pct`, `largeur_pct`, `hauteur_pct`).

Pour le DXF, convertir en coordonnées Lambert93 :
```python
lon_min, lat_min, lon_max, lat_max = parcelle.geom.bounds
# Reprojeter bbox en Lambert93
transformer = Transformer.from_crs(4326, 2154, always_xy=True)
x_min, y_min = transformer.transform(lon_min, lat_min)
x_max, y_max = transformer.transform(lon_max, lat_max)
# Calculer position absolue
x = x_min + (zone.x_pct / 100) * (x_max - x_min)
y = y_min + (zone.y_pct / 100) * (y_max - y_min)
```

### PDF et assets statiques

WeasyPrint a besoin d'accéder aux images et CSS via des chemins absolus.
Utiliser `file://` URLs pour les assets locaux en développement.
En production sur Cloudflare R2, pré-télécharger les assets nécessaires
avant la génération WeasyPrint.