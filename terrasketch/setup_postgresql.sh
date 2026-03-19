#!/bin/bash

# Configuration PostgreSQL avec PostGIS pour TerraSketch

echo "🚀 Configuration de PostgreSQL avec PostGIS pour TerraSketch..."

# Vérifier si Homebrew est installé
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew n'est pas installé. Installez-le d'abord :"
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "📦 Installation de PostgreSQL et PostGIS..."

# Installer PostgreSQL et PostGIS via Homebrew
brew install postgresql@15 postgis

# Démarrer PostgreSQL
echo "🔥 Démarrage de PostgreSQL..."
brew services start postgresql@15

# Attendre que PostgreSQL démarre
sleep 5

# Créer l'utilisateur et la base de données
echo "🗄️  Création de la base de données et de l'utilisateur..."

# Se connecter en tant qu'utilisateur par défaut et créer la DB
psql postgres << EOF
-- Créer l'utilisateur
CREATE USER terrasketch_user WITH PASSWORD 'terrasketch_pass';

-- Créer la base de données
CREATE DATABASE terrasketch_db OWNER terrasketch_user;

-- Donner les privilèges
ALTER USER terrasketch_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE terrasketch_db TO terrasketch_user;
EOF

# Activer PostGIS sur la base de données
echo "🗺️  Activation de PostGIS..."
psql -U terrasketch_user -d terrasketch_db << EOF
-- Créer l'extension PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Vérifier l'installation
SELECT PostGIS_version();
EOF

echo "✅ PostgreSQL et PostGIS configurés avec succès!"
echo ""
echo "📋 Informations de connexion :"
echo "  - Base de données: terrasketch_db"
echo "  - Utilisateur: terrasketch_user"
echo "  - Mot de passe: terrasketch_pass"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo ""
echo "🔄 Prochaines étapes :"
echo "  1. Copier .env.postgresql vers .env"
echo "  2. Exécuter les migrations Django"
echo "  3. Importer la base de données de plantes"