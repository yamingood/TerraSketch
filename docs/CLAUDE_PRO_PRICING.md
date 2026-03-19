# TerraSketch — Module Tarification Professionnelle

## Contexte

Ce module permet aux paysagistes professionnels vérifiés sur TerraSketch
de gérer leurs propres grilles tarifaires (plantes + matériaux), qui sont
ensuite utilisées automatiquement lors de la génération des devis clients.

---

## Choix architecturaux validés

| Paramètre                  | Décision                                              |
|---------------------------|-------------------------------------------------------|
| Granularité prix plantes   | Prix unique HT + coefficients de taille              |
| TVA                        | HT avec taux TVA configurable par ligne              |
| Gestion marge              | Au choix du pro : prix vente direct OU achat + %     |
| Portée géographique        | Globale — un seul tarif par pro                      |
| Mise à jour en masse       | Saisie manuelle + import CSV + ajustement global %   |
| Visibilité client          | Au choix du pro par devis                            |
| Visibilité Polsia          | Totale (back-office modération)                      |

---

## Hiérarchie des prix

```
Niveau 1 — Prix catalogue Polsia
  → Référence nationale, maintenu par Polsia via back-office
  → Utilisé si le pro n'a pas défini son propre prix

Niveau 2 — Prix pro paysagiste  ← ce module
  → Surcharge le catalogue Polsia
  → Appliqué automatiquement dans tous les devis du pro

Niveau 3 — Ajustement par devis
  → Le pro peut modifier un prix sur un devis spécifique
  → Géré dans le module devis (hors scope de ce fichier)
```

**Règle de résolution :**
```python
prix_effectif = pro_price if pro_price exists else catalog_price
```

**Règle de snapshot :**
Quand un devis est généré ou validé, tous les prix sont figés dans
`quote_line_items.price_snapshot`. Les modifications tarifaires ultérieures
du pro n'affectent jamais les devis existants.

---

## Coefficients de taille (plantes)

Le pro saisit un prix de base HT pour chaque plante (correspondant à la
taille 3L, la plus petite). TerraSketch applique automatiquement ces
coefficients selon la taille recommandée par le générateur de plan :

```python
SIZE_COEFFICIENTS = {
    "3L":    1.0,   # prix de base
    "5L":    1.6,
    "10L":   2.5,
    "15L":   3.5,
    "20L":   4.5,
    "stade": 7.0,  # arbre haute tige
}
```

Ces coefficients sont définis dans la table `size_coefficients`, gérés
par Polsia via back-office, et non modifiables par le pro.

---

## Schéma PostgreSQL

```sql
-- Coefficients de taille (gérés par Polsia)
CREATE TABLE IF NOT EXISTS size_coefficients (
    id              SERIAL PRIMARY KEY,
    size_label      VARCHAR(20) UNIQUE NOT NULL,
    coefficient     DECIMAL(4,2) NOT NULL,
    sort_order      INTEGER DEFAULT 0,
    updated_by      INTEGER REFERENCES users(id),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Prix catalogue plantes (référence Polsia)
CREATE TABLE IF NOT EXISTS plant_prices_catalog (
    id              SERIAL PRIMARY KEY,
    name_latin      VARCHAR(255) UNIQUE REFERENCES plants(name_latin),
    price_base_ht   DECIMAL(8,2) NOT NULL,
    tva_rate        DECIMAL(5,2) DEFAULT 10.00,
    updated_by      INTEGER REFERENCES users(id),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Prix catalogue matériaux (référence Polsia)
CREATE TABLE IF NOT EXISTS material_prices_catalog (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    label           VARCHAR(255) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    -- Catégories : revetement | structure | cloture | eau |
    --              eclairage | terrassement | mobilier | autre
    price_ht        DECIMAL(8,2) NOT NULL,
    unit_label      VARCHAR(20) NOT NULL,   -- "m²", "m³", "ml", "u"
    tva_rate        DECIMAL(5,2) DEFAULT 20.00,
    description     TEXT,
    updated_by      INTEGER REFERENCES users(id),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Prix plantes pro (surcharge par paysagiste)
CREATE TABLE IF NOT EXISTS pro_plant_prices (
    id                  SERIAL PRIMARY KEY,
    pro_id              INTEGER NOT NULL REFERENCES pro_profiles(id) ON DELETE CASCADE,
    name_latin          VARCHAR(255) NOT NULL REFERENCES plants(name_latin),

    -- Mode saisie
    price_mode          VARCHAR(10) NOT NULL DEFAULT 'direct'
                        CHECK (price_mode IN ('direct', 'margin')),

    -- Mode direct : le pro saisit son prix de vente HT
    price_base_ht       DECIMAL(8,2),

    -- Mode marge : le pro saisit son prix d'achat + % marge
    -- price_base_ht est calculé automatiquement via signal Django :
    -- price_base_ht = purchase_price_ht * (1 + margin_pct / 100)
    purchase_price_ht   DECIMAL(8,2),
    margin_pct          DECIMAL(5,2),

    -- TVA
    tva_rate            DECIMAL(5,2) DEFAULT 10.00,

    -- Stock
    in_stock            BOOLEAN DEFAULT TRUE,
    stock_qty           INTEGER,
    supplier_note       TEXT,       -- note interne, jamais visible client

    -- Validité
    valid_from          DATE DEFAULT CURRENT_DATE,
    valid_until         DATE,       -- NULL = pas de limite

    updated_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(pro_id, name_latin)
);

-- Prix matériaux pro (surcharge par paysagiste)
CREATE TABLE IF NOT EXISTS pro_material_prices (
    id                  SERIAL PRIMARY KEY,
    pro_id              INTEGER NOT NULL REFERENCES pro_profiles(id) ON DELETE CASCADE,
    material_slug       VARCHAR(100) NOT NULL REFERENCES material_prices_catalog(slug),

    -- Mode saisie (identique à pro_plant_prices)
    price_mode          VARCHAR(10) NOT NULL DEFAULT 'direct'
                        CHECK (price_mode IN ('direct', 'margin')),

    price_ht            DECIMAL(8,2),
    purchase_price_ht   DECIMAL(8,2),
    margin_pct          DECIMAL(5,2),

    -- TVA
    tva_rate            DECIMAL(5,2) DEFAULT 20.00,

    -- Fournisseur
    supplier_name       VARCHAR(255),
    supplier_ref        VARCHAR(100),
    unit_label          VARCHAR(20),    -- surcharge unité si différente du catalogue

    -- Validité
    valid_from          DATE DEFAULT CURRENT_DATE,
    valid_until         DATE,

    updated_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(pro_id, material_slug)
);

-- Audit trail immuable
CREATE TABLE IF NOT EXISTS pricing_audit_log (
    id              SERIAL PRIMARY KEY,
    pro_id          INTEGER REFERENCES pro_profiles(id),
    item_type       VARCHAR(20) NOT NULL,
    -- 'plant' | 'material' | 'global_plant' | 'global_material'
    item_key        VARCHAR(255),
    action          VARCHAR(20) NOT NULL,
    -- 'create' | 'update' | 'delete' | 'bulk_update' | 'csv_import' | 'reset_catalog'
    old_values      JSONB,
    new_values      JSONB,
    changed_by      INTEGER REFERENCES users(id),
    changed_at      TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS pro_plant_prices_pro_idx
    ON pro_plant_prices(pro_id);
CREATE INDEX IF NOT EXISTS pro_plant_prices_latin_idx
    ON pro_plant_prices(name_latin);
CREATE INDEX IF NOT EXISTS pro_material_prices_pro_idx
    ON pro_material_prices(pro_id);
CREATE INDEX IF NOT EXISTS pricing_audit_pro_idx
    ON pricing_audit_log(pro_id, changed_at DESC);
```

---

## Structure des fichiers à créer

```
pricing/
  __init__.py
  models.py                    # Modèles Django
  serializers.py               # DRF serializers
  views.py                     # Endpoints API
  urls.py                      # Routing
  signals.py                   # Calcul auto price_ht mode marge + audit log
  admin.py                     # Back-office Polsia
  permissions.py               # IsProVerified, IsPolsiaAdmin
  services/
    __init__.py
    price_resolver.py          # Résolution prix effectif
    bulk_updater.py            # Ajustement % global + reset catalogue
    csv_handler.py             # Import/export CSV
  tests/
    __init__.py
    test_price_resolver.py
    test_bulk_updater.py
    test_csv_handler.py
    test_views.py
    fixtures/
      sample_plant_prices.csv
      sample_material_prices.csv
  migrations/
    0001_initial.py
```

---

## Tâche 1 — Modèles Django `pricing/models.py`

Créer les modèles correspondant au schéma SQL.

Points critiques sur `ProPlantPrice` et `ProMaterialPrice` :

```python
@property
def effective_price_ht(self) -> Decimal:
    """Prix HT effectif quelle que soit le mode de saisie."""
    if self.price_mode == 'direct':
        return self.price_base_ht
    # mode margin
    return self.purchase_price_ht * (Decimal('1') + self.margin_pct / 100)

def save(self, *args, **kwargs):
    # Synchroniser price_base_ht depuis le calcul marge
    if self.price_mode == 'margin':
        self.price_base_ht = self.effective_price_ht
    super().save(*args, **kwargs)

def is_valid(self) -> bool:
    """Retourne True si le prix est actif aujourd'hui."""
    today = date.today()
    if self.valid_from and self.valid_from > today:
        return False
    if self.valid_until and self.valid_until < today:
        return False
    return True
```

---

## Tâche 2 — Signals Django `pricing/signals.py`

```python
@receiver(post_save, sender=ProPlantPrice)
def log_plant_price_change(sender, instance, created, **kwargs):
    """
    Logge chaque création/modification dans pricing_audit_log.
    Capturer old_values depuis instance.__original si disponible.
    """

@receiver(post_save, sender=ProMaterialPrice)
def log_material_price_change(sender, instance, created, **kwargs): ...

@receiver(post_delete, sender=ProPlantPrice)
def log_plant_price_deletion(sender, instance, **kwargs): ...

@receiver(post_delete, sender=ProMaterialPrice)
def log_material_price_deletion(sender, instance, **kwargs): ...
```

Pour capturer `old_values`, utiliser le pattern `__init__` override :

```python
class ProPlantPrice(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot des valeurs à l'initialisation pour diff dans le signal
        self.__original_price_base_ht = self.price_base_ht
        self.__original_tva_rate = self.tva_rate
```

---

## Tâche 3 — Service de résolution `pricing/services/price_resolver.py`

```python
def resolve_plant_price(name_latin: str, pro_id: int, size_label: str = "3L") -> dict:
    """
    Retourne le prix effectif d'une plante pour un pro, à la taille demandée.

    Algorithme :
    1. Chercher ProPlantPrice (pro_id + name_latin) → vérifier is_valid()
    2. Si absent ou invalide → chercher PlantPricesCatalog
    3. Charger SizeCoefficient pour size_label
    4. Calculer price_ht_final = price_base_ht × coefficient

    Retourne :
    {
        "name_latin": str,
        "size_label": str,
        "price_base_ht": Decimal,       # prix 3L (avant coefficient)
        "coefficient": Decimal,
        "price_ht": Decimal,            # price_base_ht × coefficient
        "tva_rate": Decimal,
        "price_ttc": Decimal,           # price_ht × (1 + tva_rate/100)
        "source": "pro" | "catalog",
        "in_stock": bool,
        "valid_until": date | None,
    }
    Lève PriceNotFoundError si absent du catalogue aussi.
    """


def resolve_material_price(material_slug: str, pro_id: int) -> dict:
    """
    Identique sans coefficient de taille.

    Retourne :
    {
        "material_slug": str,
        "label": str,
        "price_ht": Decimal,
        "tva_rate": Decimal,
        "price_ttc": Decimal,
        "unit_label": str,
        "source": "pro" | "catalog",
        "supplier_name": str | None,
    }
    """


def resolve_plan_budget(plan_json: dict, pro_id: int) -> dict:
    """
    Calcule le budget complet d'un plan IA.
    Parcourt plan_json["plantes"] et plan_json["zones"] (matériaux).

    Pour les plantes : utiliser size_label recommandé dans le plan,
    défaut "5L" si absent (taille standard jardin).

    Retourne :
    {
        "lignes_plantes": [
            {
                "name_latin", "name_common", "size_label",
                "quantite": int,
                "prix_unitaire_ht": Decimal,
                "prix_total_ht": Decimal,
                "tva_rate": Decimal,
                "prix_total_ttc": Decimal,
                "source": "pro" | "catalog",
                "in_stock": bool,
            }
        ],
        "lignes_materiaux": [...],
        "sous_total_plantes_ht": Decimal,
        "sous_total_materiaux_ht": Decimal,
        "sous_total_ht": Decimal,
        "total_tva": Decimal,
        "total_ttc": Decimal,
        "phases": [
            {
                "numero": int,
                "nom": str,
                "sous_total_ht": Decimal,
                "total_ttc": Decimal,
            }
        ],
        "items_sans_prix": [str],   # plantes/matériaux sans aucun prix défini
        "source_mix": {
            "pro_pct": float,       # % budget basé sur prix pro
            "catalog_pct": float,
        }
    }
    """
```

---

## Tâche 4 — Service mise à jour en masse `pricing/services/bulk_updater.py`

```python
def apply_global_percentage(
    pro_id: int,
    percentage: float,          # positif = hausse, négatif = baisse
    scope: str,                 # "plants" | "materials" | "all"
    category: str = None,       # filtrer catégorie matériaux (optionnel)
    round_to: int = 2,
) -> dict:
    """
    Applique un % sur price_base_ht (mode direct) ou margin_pct (mode marge).
    Logger dans pricing_audit_log avec action='bulk_update'.
    Retourne : {"updated_plants": int, "updated_materials": int}
    """


def reset_to_catalog(
    pro_id: int,
    scope: str,                 # "plants" | "materials" | "all"
    name_latin: str = None,     # reset une seule plante si fourni
    material_slug: str = None,  # reset un seul matériau si fourni
) -> dict:
    """
    Supprime les prix pro → retour au catalogue Polsia.
    Logger avec action='reset_catalog'.
    Retourne : {"deleted_plants": int, "deleted_materials": int}
    """
```

---

## Tâche 5 — Gestion CSV `pricing/services/csv_handler.py`

### Format CSV plantes attendu

```
name_latin,price_mode,price_base_ht,tva_rate,purchase_price_ht,margin_pct,in_stock,valid_until,supplier_note
Lavandula angustifolia,direct,4.50,10.00,,,true,,
Buxus sempervirens,margin,,10.00,3.00,50.00,true,2025-12-31,Pépinière Martin
```

### Format CSV matériaux attendu

```
material_slug,price_mode,price_ht,tva_rate,purchase_price_ht,margin_pct,supplier_name,supplier_ref,valid_until
terrasse_bois_ipe,direct,85.00,20.00,,,Bois & Co,REF-IPE,
gravier_blanc,margin,,20.00,30.00,50.00,Granulats Sud,GR-BL,2025-06-30
```

```python
def import_plant_prices_csv(pro_id: int, file_path: str, mode: str = "upsert") -> dict:
    """
    Validations ligne par ligne :
    - name_latin doit exister dans plants
    - price_base_ht OU (purchase_price_ht + margin_pct) requis selon price_mode
    - tva_rate entre 0 et 100
    - valid_until au format YYYY-MM-DD

    mode "upsert"      → update existants + créer nouveaux
    mode "replace_all" → supprimer tous les prix pro puis importer

    Retourne :
    {"imported": int, "updated": int, "skipped": int,
     "errors": [{"line": int, "name_latin": str, "error": str}]}
    """

def import_material_prices_csv(pro_id: int, file_path: str, mode: str = "upsert") -> dict:
    """Identique, valider material_slug dans material_prices_catalog."""

def export_plant_prices_csv(pro_id: int) -> str:
    """
    Exporte les prix pro au format CSV.
    Inclure price_base_ht calculé même en mode marge.
    Retourne le contenu CSV (string).
    """

def export_material_prices_csv(pro_id: int) -> str:
    """Identique pour les matériaux."""

def generate_template_csv(item_type: str) -> str:
    """
    Template CSV vide avec en-têtes + une ligne exemple commentée (#).
    item_type : "plants" | "materials"
    """
```

---

## Tâche 6 — Endpoints DRF `pricing/views.py`

### Plantes

```
GET    /api/pro/pricing/plants/
       Liste tous les prix plantes du pro.
       Query params : ?in_stock=true, ?search=lavande, ?has_price=true|false
       Retourne : liste avec source "pro" | "catalog" et prix effectif

POST   /api/pro/pricing/plants/
       Crée ou met à jour le prix d'une plante (upsert sur name_latin).

PATCH  /api/pro/pricing/plants/{name_latin}/
       Mise à jour partielle.

DELETE /api/pro/pricing/plants/{name_latin}/
       Supprime le prix pro (retour catalogue Polsia).

POST   /api/pro/pricing/plants/bulk-percentage/
       Body : {percentage: float, scope: "plants"|"materials"|"all"}

POST   /api/pro/pricing/plants/import-csv/
       Multipart. Body : {file: File, mode: "upsert"|"replace_all"}

GET    /api/pro/pricing/plants/export-csv/
       Réponse : fichier CSV en téléchargement.

GET    /api/pro/pricing/plants/template-csv/
       Réponse : fichier CSV template en téléchargement.
```

### Matériaux

```
GET    /api/pro/pricing/materials/
       Query params : ?category=revetement, ?search=gravier

POST   /api/pro/pricing/materials/
PATCH  /api/pro/pricing/materials/{material_slug}/
DELETE /api/pro/pricing/materials/{material_slug}/
POST   /api/pro/pricing/materials/bulk-percentage/
POST   /api/pro/pricing/materials/import-csv/
GET    /api/pro/pricing/materials/export-csv/
GET    /api/pro/pricing/materials/template-csv/
```

### Budget plan (usage interne)

```
POST   /api/pro/pricing/resolve-budget/
       Body : {plan_json: {...}, pro_id: int}
       Appelé par le service de génération de plan.
       Permission : IsAuthenticated (pas besoin d'être pro)
```

### Back-office Polsia

```
GET    /api/admin/pricing/pros/{pro_id}/plants/
GET    /api/admin/pricing/pros/{pro_id}/materials/
       Permission : IsPolsiaAdmin uniquement.

GET    /api/admin/pricing/audit-log/
       Query params : ?pro_id=, ?action=, ?date_from=, ?date_to=
       Journal complet immuable.

GET    /api/admin/pricing/catalog/plants/
PUT    /api/admin/pricing/catalog/plants/{name_latin}/
GET    /api/admin/pricing/catalog/materials/
PUT    /api/admin/pricing/catalog/materials/{slug}/
       Gestion du catalogue de référence Polsia.
```

---

## Tâche 7 — Visibilité devis client

Ajouter sur le modèle `Quote` existant :

```python
# Contrôle visibilité dans le PDF/aperçu client
show_unit_prices        = BooleanField(default=True)
# True  → client voit prix unitaire × quantité = total par ligne
# False → client voit seulement les totaux

show_plant_details      = BooleanField(default=True)
# True  → liste des plantes nommées avec prix
# False → regroupé en "Fournitures végétales"

show_material_details   = BooleanField(default=True)
# True  → liste des matériaux avec prix
# False → regroupé en "Fournitures et matériaux"
```

Ces champs sont configurables depuis l'interface de prévisualisation
du devis, avant envoi au client.

---

## Tâche 8 — Permissions `pricing/permissions.py`

```python
class IsProVerified(BasePermission):
    """
    Autorise uniquement les pros avec statut 'verified' dans pro_profiles.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'pro_profile') and
            request.user.pro_profile.status == 'verified'
        )

class IsOwnProProfile(BasePermission):
    """
    Vérifie que le pro accède uniquement à ses propres données tarifaires.
    """
    def has_object_permission(self, request, view, obj):
        return obj.pro_id == request.user.pro_profile.id

class IsPolsiaAdmin(BasePermission):
    """
    Autorise uniquement les admins Polsia (is_staff=True).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff
```

---

## Tâche 9 — Admin Django `pricing/admin.py`

Enregistrer avec ces configurations :

- `SizeCoefficients` — CRUD complet
- `PlantPricesCatalog` — CRUD + import CSV bulk
- `MaterialPricesCatalog` — CRUD + import CSV bulk, filtres par category
- `ProPlantPrice` — lecture seule, filtres par pro_id + name_latin
- `ProMaterialPrice` — lecture seule, filtres par pro_id + category
- `PricingAuditLog` — lecture seule uniquement, aucune modification possible,
  filtres par pro_id + action + date

---

## Tâche 10 — Composant React `ProPricingManager.jsx`

Créer `frontend/src/components/pro/ProPricingManager.jsx`.

### États et structure

```
ProPricingManager
├── Header
│   ├── "Mes Tarifs"
│   ├── Bouton "Importer CSV"
│   ├── Bouton "Exporter CSV"
│   └── Bouton "Ajustement global %"
│
├── Tabs : "Plantes" (badge nb prix pro) | "Matériaux" (badge nb prix pro)
│
├── Tab Plantes
│   ├── Barre recherche (filtre temps réel côté client)
│   ├── Chips filtre : Tous | Prix pro défini | En stock | Expirés bientôt
│   └── Tableau
│       Colonnes :
│         Plante | Prix catalogue (gris) | Mode | Mon prix HT | TVA% | TTC | Stock | Actions
│       - "Mon prix" affiché en vert si défini, "—" (catalogue) si absent
│       - Badge orange si valid_until < 30 jours
│       - Aperçu tailles au survol (tooltip 3L/5L/10L avec prix calculés)
│       - Actions : [Modifier] [Reset catalogue]
│
├── Tab Matériaux
│   ├── Chips catégories : Revêtements | Structure | Clôture | Eau | ...
│   ├── Barre recherche
│   └── Tableau identique structure Tab Plantes
│
├── Modal "Modifier prix plante/matériau"
│   ├── Toggle : "Prix de vente" | "Prix achat + marge"
│   │
│   ├── Si "Prix de vente" :
│   │   ├── Champ Prix HT (€)
│   │   └── Sélecteur TVA (5.5% | 10% | 20%)
│   │
│   ├── Si "Prix achat + marge" :
│   │   ├── Champ Prix achat HT (€)
│   │   ├── Champ Marge (%)
│   │   └── Affichage calculé : "Prix de vente = X,XX €HT"
│   │
│   ├── [Plantes uniquement] Tableau aperçu tailles :
│   │   3L → X,XX€ | 5L → X,XX€ | 10L → X,XX€ | 15L → X,XX€
│   │
│   ├── Toggle En stock + champ Quantité (optionnel)
│   ├── Date valable jusqu'au (optionnel, datepicker)
│   ├── Note fournisseur (textarea, non visible client)
│   └── Boutons : [Annuler] [Enregistrer]
│
├── Modal "Ajustement global %"
│   ├── Champ % avec indicateur +/- coloré
│   ├── Radio : Plantes | Matériaux | Tout
│   ├── Si Matériaux : filtre catégorie (optionnel)
│   ├── Aperçu : "X prix seront ajustés de Y%"
│   └── Boutons : [Annuler] [Appliquer]
│
└── Modal "Import CSV"
    ├── Zone drag & drop
    ├── Lien "Télécharger le template"
    ├── Radio : Fusion (upsert) | Remplacement total
    │   Avertissement si "Remplacement total" sélectionné
    └── Après import : résumé {X créés, Y mis à jour, Z erreurs}
        Si erreurs : tableau des lignes en erreur téléchargeable
```

### Props

```jsx
<ProPricingManager
  proId={number}
  onPriceUpdated={() => void}   // rafraîchir les devis ouverts si prix modifiés
/>
```

---

## Tâche 11 — Tests

### `test_price_resolver.py`

```
test_resolve_plant_price_pro_defined
  → Pro a un prix → retourner prix pro + coefficient taille 3L

test_resolve_plant_price_fallback_catalog
  → Pas de prix pro → retourner prix catalogue, source="catalog"

test_resolve_plant_price_size_coefficient_10L
  → Demander 10L, coefficient 2.5 → vérifier price_ht = base × 2.5

test_resolve_plant_price_expired_valid_until
  → valid_until = hier → fallback catalogue

test_resolve_plant_price_margin_mode
  → purchase=10€, margin=50% → price_base_ht=15€

test_resolve_material_no_coefficient
  → Material → vérifier pas de coefficient appliqué

test_resolve_plan_budget_totals
  → Plan avec 3 plantes (quantités) et 2 matériaux
  → Vérifier sous-totaux, TVA, TTC exacts

test_resolve_plan_budget_phases
  → Plan avec 2 phases → vérifier ventilation par phase correcte

test_resolve_plan_budget_missing_item
  → Plante absente du catalogue → dans items_sans_prix
```

### `test_bulk_updater.py`

```
test_global_percentage_plus_10_plants
  → +10% sur toutes les plantes → chaque price_base_ht augmenté de 10%

test_global_percentage_minus_5_materials_category
  → -5% sur catégorie "revetement" → seuls ces matériaux modifiés

test_global_percentage_margin_mode
  → Pro en mode marge → margin_pct ajusté, pas price_base_ht direct

test_reset_single_plant
  → Reset Lavandula → entrée supprimée, catalogue utilisé ensuite

test_reset_all_creates_audit_log
  → Reset tout → nb entrées audit_log == nb prix supprimés
```

### `test_csv_handler.py`

```
test_import_plants_csv_upsert_mode
  → 3 plantes CSV, 1 déjà en base → 2 créées, 1 mise à jour

test_import_plants_csv_unknown_latin
  → name_latin inconnu → ligne en erreur, reste importé normalement

test_import_plants_csv_missing_price_fields
  → Ni price_base_ht ni purchase_price_ht → ligne en erreur

test_import_materials_replace_all
  → 5 matériaux existants + CSV 3 nouveaux → résultat : 3 uniquement

test_export_import_roundtrip
  → Créer 5 prix → exporter → supprimer → réimporter → identiques

test_template_csv_has_all_columns
  → Vérifier présence de chaque colonne attendue
```

### `test_views.py` (APITestCase)

```
test_list_plants_authenticated_pro
test_list_plants_unauthenticated_returns_403
test_list_plants_unverified_pro_returns_403
test_create_plant_price_direct_mode_returns_201
test_create_plant_price_margin_mode_calculates_price_ht
test_patch_plant_price_partial_update
test_delete_plant_price_resets_to_catalog
test_bulk_percentage_endpoint_returns_counts
test_csv_import_endpoint_returns_summary
test_csv_export_endpoint_returns_csv_file
test_polsia_admin_sees_all_pros_prices
test_pro_cannot_see_other_pro_prices_403
test_audit_log_readable_by_polsia_only
```

---

## Tâche 12 — Migration `pricing/migrations/0001_initial.py`

Créer la migration Django dans l'ordre des dépendances FK :
1. `size_coefficients`
2. `plant_prices_catalog`
3. `material_prices_catalog`
4. `pro_plant_prices`
5. `pro_material_prices`
6. `pricing_audit_log`

Inclure un `RunPython` pour les données initiales :

```python
def insert_initial_data(apps, schema_editor):
    SizeCoefficients = apps.get_model('pricing', 'SizeCoefficients')
    SizeCoefficients.objects.bulk_create([
        SizeCoefficients(size_label="3L",    coefficient=1.0,  sort_order=1),
        SizeCoefficients(size_label="5L",    coefficient=1.6,  sort_order=2),
        SizeCoefficients(size_label="10L",   coefficient=2.5,  sort_order=3),
        SizeCoefficients(size_label="15L",   coefficient=3.5,  sort_order=4),
        SizeCoefficients(size_label="20L",   coefficient=4.5,  sort_order=5),
        SizeCoefficients(size_label="stade", coefficient=7.0,  sort_order=6),
    ])
```

---

## Notes importantes

### TVA en France
- Plantes et végétaux : **10%** (taux intermédiaire horticole)
- Matériaux de construction/aménagement : **20%** (taux normal)
- Ces valeurs sont les défauts. Le pro peut ajuster par ligne si nécessaire
  (ex: fournitures mixtes, régimes particuliers agricoles).

### Intégration avec le générateur de plan
`resolve_plan_budget()` est appelé automatiquement après chaque génération
de plan IA. Le `pro_id` est résolu depuis le contexte de la session :
- Utilisateur est un pro vérifié → ses prix
- Utilisateur particulier associé à un pro → prix du pro associé
- Aucun pro → catalogue Polsia uniquement

### Sécurité et isolation
- Chaque endpoint pro vérifie `pro_id == request.user.pro_profile.id`
- Un pro ne peut jamais lire ni modifier les prix d'un autre pro
- Seuls les admins Polsia (`IsPolsiaAdmin`) accèdent aux endpoints `/api/admin/pricing/`
- Le `pricing_audit_log` est en écriture uniquement via signals Django —
  aucun endpoint de modification, immuable par design