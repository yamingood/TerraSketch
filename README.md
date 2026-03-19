# TerraSketch - Plateforme SaaS de conception paysagère automatisée

TerraSketch est une plateforme SaaS développée par Polsia qui transforme un plan cadastral en aménagement paysager complet visualisable en 2D et 3D.

## Architecture

- **Backend**: Django 5.x + PostgreSQL/PostGIS + Redis + Celery
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **IA**: Claude API (Anthropic) pour la génération automatisée
- **Déploiement**: Railway (backend) + Vercel (frontend)

## Structure du projet

```
terrasketch-project/
├── terrasketch/           # Backend Django
│   ├── config/           # Configuration Django
│   ├── apps/             # Applications Django
│   │   ├── accounts/     # Gestion utilisateurs
│   │   ├── projects/     # Projets paysagers
│   │   ├── plants/       # Bibliothèque végétale
│   │   ├── designs/      # Conceptions IA
│   │   ├── budget/       # Module budget
│   │   ├── care/         # Calendrier entretien
│   │   ├── professionals/# Espace paysagistes
│   │   └── backoffice/   # Administration Polsia
│   ├── core/             # Permissions, utils partagés
│   ├── integrations/     # APIs externes (Claude, Stripe, IGN)
│   └── tests/            # Tests
└── terrasketch-front/     # Frontend React
    └── src/
        ├── pages/        # Pages de l'application
        ├── components/   # Composants réutilisables
        ├── hooks/        # Hooks React personnalisés
        ├── stores/       # État global (Zustand)
        ├── api/          # Clients API
        └── lib/          # Utilitaires

```

## Phases de développement

### Phase 1 - MVP (T1 2025) - EN COURS
- ✅ Structure des dossiers
- ⏳ Auth + abonnements Stripe
- ⏳ Import plan cadastral (PDF/DXF)
- ⏳ Module budget basique
- ⏳ Génération IA plan 2D (styles Méditerranéen + Contemporain)
- ⏳ Export PNG du plan
- ⏳ Bibliothèque végétale (100 espèces)

### Phase 2 - Beta Pro (T2 2025)
- Éditeur 2D drag & drop
- Visualisation 3D
- Simulation temporelle
- Espace professionnel
- Back-office Polsia

### Phase 3 - Scale (T3-T4 2025)
- API IGN cadastre automatique
- Bibliothèque complète (500+ espèces)
- Alertes météo
- Rendus photoréalistes

## Installation

Voir les README spécifiques dans chaque dossier :
- [Backend Setup](./terrasketch/README.md)
- [Frontend Setup](./terrasketch-front/README.md)

## Variables d'environnement

Copier `.env.example` vers `.env.local` et remplir les valeurs.

## Support

Développé par Polsia - 2025