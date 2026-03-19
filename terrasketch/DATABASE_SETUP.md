# Configuration de la Base de Données TerraSketch

Ce document explique comment configurer la base de données pour TerraSketch avec soit SQLite (développement) soit PostgreSQL avec PostGIS (production).

## 🚀 Configuration Rapide (SQLite)

Pour une configuration rapide de développement avec SQLite :

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Configuration automatique
python setup_database.py
```

## 🗄️ Configuration PostgreSQL + PostGIS (Production)

### Prérequis
- PostgreSQL 15+
- PostGIS
- Homebrew (macOS)

### Installation automatique

```bash
# Exécuter le script de configuration PostgreSQL
./setup_postgresql.sh
```

### Configuration manuelle

1. **Installation des dépendances**
```bash
brew install postgresql@15 postgis
brew services start postgresql@15
```

2. **Création de la base de données**
```sql
-- Se connecter à PostgreSQL
psql postgres

-- Créer l'utilisateur et la base de données
CREATE USER terrasketch_user WITH PASSWORD 'terrasketch_pass';
CREATE DATABASE terrasketch_db OWNER terrasketch_user;
GRANT ALL PRIVILEGES ON DATABASE terrasketch_db TO terrasketch_user;

-- Activer PostGIS
\c terrasketch_db
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

3. **Configuration Django**
```bash
# Copier le fichier de configuration
cp .env.postgresql .env

# Modifier les paramètres si nécessaire
# DB_NAME, DB_USER, DB_PASSWORD, etc.
```

4. **Migrations et données**
```bash
# Utiliser la configuration PostgreSQL
export DJANGO_SETTINGS_MODULE=config.settings.postgresql

# Migrations Django
python manage.py migrate

# Importer les données
python create_test_user.py
python import_plants_database.py
```

## 📊 Base de Données de Plantes

Le fichier `terrasketch_plants_database.json` contient :
- **160 espèces de plantes** avec données botaniques complètes
- **70+ familles botaniques**
- Informations détaillées : exposition, besoins en eau, résistance au froid
- Styles d'aménagement et affinités
- Catégorisation par types (arbres, arbustes, vivaces, etc.)

### Structure des données

```json
{
  "name_latin": "Nom scientifique",
  "name_common": "Nom commun français", 
  "family": "Famille botanique",
  "category": "Type de plante",
  "size_adult_height": "Hauteur adulte (m)",
  "sun_requirements": "Exposition solaire",
  "watering_needs": "Besoins en eau",
  "hardiness_zone": "Zone de rusticité",
  "styles": ["Styles d'aménagement"],
  "climate_zones": ["Zones climatiques"]
}
```

## 🔧 Scripts Utilitaires

- `setup_database.py` : Configuration complète automatique
- `setup_postgresql.sh` : Installation PostgreSQL + PostGIS  
- `import_plants_database.py` : Import de la base de données de plantes
- `create_test_user.py` : Création d'un utilisateur de test

## 📈 Vérification

Après configuration, vérifiez avec :

```bash
# Démarrer le serveur
python manage.py runserver

# Tester les APIs
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "testeur@terrasketch.com", "password": "password123"}'

# Tester la liste des plantes (avec token JWT)
curl -X GET "http://localhost:8000/api/plants/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🚨 Résolution de Problèmes

### PostGIS non trouvé
```bash
# Vérifier l'installation
brew list | grep postgis

# Réinstaller si nécessaire
brew reinstall postgis
```

### Erreurs de migration
```bash
# Reset des migrations (développement uniquement)
python manage.py migrate --fake-initial

# Ou supprimer les fichiers de migration et recréer
rm apps/*/migrations/00*.py
python manage.py makemigrations
python manage.py migrate
```

### Permissions PostgreSQL
```sql
-- Donner tous les privilèges
ALTER USER terrasketch_user SUPERUSER;
-- ou spécifiquement
GRANT ALL ON ALL TABLES IN SCHEMA public TO terrasketch_user;
```

## 📝 Configuration Files

- `.env.postgresql` : Variables d'environnement PostgreSQL
- `config/settings/postgresql.py` : Configuration Django PostgreSQL
- `config/settings/migration_minimal.py` : Configuration minimale SQLite