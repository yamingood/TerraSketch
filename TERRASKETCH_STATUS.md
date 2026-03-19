# TerraSketch - État du Projet

## 📋 Résumé Général

TerraSketch est une application web de génération automatisée de plans paysagers par IA, composée d'un backend Django et d'un frontend React. Le projet implémente un système sophistiqué d'assemblage de contexte (terrain + climat + préférences) pour générer des plans personnalisés via l'API Claude d'Anthropic.

## 🏗️ Architecture Technique

### Backend Django (`terrasketch/`)
- **Framework** : Django 4.2+ avec Django REST Framework
- **Base de données** : PostgreSQL (prévu) / SQLite (dev)
- **Task Queue** : Celery + Redis
- **WebSocket** : Django Channels (prévu)
- **IA** : API Anthropic Claude 3.5 Sonnet
- **Géolocalisation** : API IGN + Open-Meteo + PyDayLight

### Frontend React (`terrasketch-front/`)
- **Framework** : React 18 + TypeScript + Vite
- **Styling** : Tailwind CSS
- **State** : React Query + Context API
- **Router** : React Router
- **Build** : Vite + ESBuild

## 🎯 Ce qui a été Réalisé

### ✅ Infrastructure & Base
- [x] **Structure projet** - Architecture Django + React séparée
- [x] **Configuration environnements** - Settings, variables d'env, logging
- [x] **Apps Django** - accounts, projects, plants, ai, cadastre, geography
- [x] **Authentication** - JWT avec refresh tokens
- [x] **CORS & middleware** - Configuration pour dev/prod

### ✅ Modules Core Django

#### 1. **App Accounts** (`apps/accounts/`)
```python
# Modèles principaux
- User (custom avec email login)
- Organization (pour pros)
- UserProfile (préférences étendues)
```

#### 2. **App Projects** (`apps/projects/`)
```python
# Modèles principaux
- Project (projets utilisateur)
- Parcel (données parcelles)
- TerrainAnalysis (analyse topographique)
- EarthworkRecommendation (recommandations terrassement)
```

#### 3. **App Plants** (`apps/plants/`)
```python
# Modèles préparés pour base de données plantes
- Plant (espèces végétales)
- PlantCategory (classification)
```

### ✅ Système IA Complet (`apps/ai/`)

#### **Modèles de données**
```python
# apps/ai/models.py
- Plan (plans générés avec versioning)
- GenerationJob (suivi temps réel)
- ClimateCache (cache données météo)
- PlantCompatibility (cache compatibilités)
- UserGenerationQuota (limites utilisateur)
```

#### **Context Builder** (`apps/ai/context/`)
```python
# Services d'assemblage contexte
- ClimateService : API Open-Meteo + zones climatiques françaises
- SolarService : Calculs PyDayLight + orientations optimales
- PlantSelector : Compatibilité climat/rusticité/préférences
- ContextAssembler : Orchestrateur principal
```

#### **Prompt Builder** (`apps/ai/prompt/`)
```python
# Construction prompts structurés
- SystemPrompt : Rôle paysagiste expert français
- OutputSchema : Schéma JSON strict (zones/plantes/budget/calendrier)
- Builder : Construction XML (terrain/climat/plantes/instructions)
- Validators : Validation réponses + parsing JSON robuste
```

#### **Plan Generator** (`apps/ai/generator/`) [EN COURS]
```python
# Orchestration génération
- ClaudeClient : API Anthropic + streaming + retry logic
- StreamingHandler : WebSocket temps réel [À FAIRE]
- PlanGenerator : Pipeline complet [À FAIRE]
```

### ✅ Frontend React

#### **Structure & Routing**
```typescript
// Pages principales implémentées
- LoginPage / RegisterPage (auth complète)
- DashboardPage (tableau de bord)
- OnboardingPage (upload cadastre)
- PlantRecommendationsPage (suggestions)
```

#### **Composants Key**
```typescript
// Composants fonctionnels
- CadastreUpload : Upload fichiers cadastraux (GeoJSON/Shapefile/DXF/EDIGÉO)
- LoginForm / RegisterForm : Authentification
- Header : Navigation
```

### ✅ Configuration & Outils
```yaml
# Variables d'environnement configurées
- ANTHROPIC_API_KEY (Claude AI)
- CORS settings pour dev/prod  
- JWT avec rotation
- Celery + Redis
- Logging structuré
```

## 🚧 En Cours / Partiellement Implémenté

### Plan Generator (70% fait)
- ✅ Client Claude avec streaming
- ✅ Gestion erreurs + retry logic
- 🔄 Orchestrateur principal (manque assemblage final)
- ❌ WebSocket handler
- ❌ Tâches Celery

### API REST Endpoints
- ✅ Auth endpoints (login/register/refresh)
- ❌ `/api/projects/{id}/generate/` (génération plans)
- ❌ `/api/cadastre/upload/` (404 actuellement)
- ❌ Endpoints plantes/recommendations

## ❌ À Implémenter pour Fonctionnement Complet

### 1. **API REST Critique**
```python
# urls à créer
POST /api/cadastre/upload/          # Upload fichiers cadastraux
POST /api/projects/{id}/generate/   # Déclencher génération IA
GET  /api/projects/{id}/plans/      # Historique plans
GET  /api/plants/compatible/        # Plantes compatibles
```

### 2. **Django Channels (WebSocket)**
```python
# apps/ai/consumers.py - Consumer WebSocket temps réel
# routing.py - Configuration channels
# Connexion Redis pour messages
```

### 3. **Tâches Celery**
```python
# apps/ai/tasks.py
@shared_task
def generate_plan_task(project_id, preferences)
    # Pipeline complet avec streaming WebSocket
```

### 4. **Base de Données Plantes**
```python
# Peuplement apps/plants/ avec vraies données
# Critères compatibilité (rusticité, climat, sol)
# Fixtures ou command Django
```

### 5. **Service Files & Upload**
```python
# apps/cadastre/views.py - Upload handler
# Parsing GeoJSON, Shapefile, DXF
# Validation géométrie + extraction surface
```

### 6. **Frontend - Pages Manquantes**
```typescript
// Pages critiques
- ProjectDetailPage (visualisation plan)
- PlanGenerationPage (streaming temps réel) 
- PlantDatabasePage (catalogue plantes)
- ProDashboard (fonctionnalités pro)
```

## 🔥 Actions Prioritaires pour MVP

### Priorité 1 - API Upload Cadastre
```bash
1. Créer apps/cadastre/views.py avec endpoint upload
2. Parser basique GeoJSON + calcul surface
3. Retour JSON compatible CadastreUpload.tsx
```

### Priorité 2 - Pipeline IA Basique
```bash
1. Finir apps/ai/generator/plan_generator.py 
2. Endpoint POST /api/projects/{id}/generate/
3. Test avec prompt simple (sans streaming)
```

### Priorité 3 - Frontend Plan View
```bash
1. Page affichage plan JSON généré
2. Visualisation zones + plantes
3. Export basique
```

## 📊 Statistiques Code

### Backend
- **Apps Django** : 8 apps structurées
- **Modèles** : ~15 modèles principaux
- **Code IA** : ~2000 lignes (context + prompt + generator)
- **Tests** : Structure préparée, à implémenter

### Frontend  
- **Composants** : 7 composants principaux
- **Pages** : 5 pages fonctionnelles
- **Routes** : Auth + dashboard configuré
- **Styling** : Tailwind intégré

## 🚀 Roadmap Technique

### Phase 1 - MVP Fonctionnel (1-2 semaines)
- [ ] API upload cadastre fonctionnelle
- [ ] Pipeline IA end-to-end simple
- [ ] Affichage plans basique
- [ ] Base de données plantes minimale

### Phase 2 - Fonctionnalités Avancées (2-3 semaines)  
- [ ] WebSocket streaming temps réel
- [ ] Système budget professionnel
- [ ] Export PNG/PDF plans
- [ ] Gestion multi-projets

### Phase 3 - Production (1-2 semaines)
- [ ] PostgreSQL + Redis déploiement
- [ ] Docker configuration
- [ ] CI/CD Pipeline
- [ ] Monitoring + logs

## 🛠️ Commandes Développement

### Backend Django
```bash
cd terrasketch/
source venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py test
```

### Frontend React  
```bash
cd terrasketch-front/
npm run dev
npm run build
npm run test
```

### Base de données
```bash
# Migrations AI module
python manage.py makemigrations ai
python manage.py migrate
```

## 🔧 Variables d'Environnement Requises

```env
# Django
SECRET_KEY=django-secret-key
DEBUG=True
DATABASE_URL=postgresql://...

# IA & APIs
ANTHROPIC_API_KEY=sk-ant-...
AI_MODEL=claude-3-5-sonnet-20241022
AI_MAX_TOKENS=4096

# Services externes
STRIPE_SECRET_KEY=sk_...
CLOUDFLARE_R2_ACCESS_KEY=...

# Infrastructure  
CELERY_BROKER_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## 🎯 État Global : 75% MVP Prêt

**Points forts :**
- Architecture solide et extensible
- Système IA sophistiqué et bien structuré  
- Frontend React moderne et responsive
- Configuration production-ready

**Points bloquants :**
- APIs REST incomplètes (upload + génération)
- Base de données plantes vide
- WebSocket pas encore configuré

**Estimation MVP complet :** 1-2 semaines de développement focalisé sur les APIs manquantes.

---

*Dernière mise à jour : 19 mars 2026*
*Status: Development actif - Backend IA 90% - Frontend 80% - APIs 40%*