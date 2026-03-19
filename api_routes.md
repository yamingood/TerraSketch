# TerraSketch API Routes

Base URL: `/api/v1/`
Format: JSON
Auth: JWT Bearer Token

## Auth
- `POST /auth/register/` - Inscription
- `POST /auth/login/` - Connexion
- `POST /auth/refresh/` - Renouveler token
- `POST /auth/logout/` - Déconnexion
- `POST /auth/verify-email/` - Vérification email
- `POST /auth/password-reset/` - Reset password
- `POST /auth/password-reset/confirm/` - Confirmer reset
- `GET /auth/me/` - Profil utilisateur
- `PUT /auth/me/` - Mise à jour profil

## Projets
- `GET /projects/` - Liste des projets
- `POST /projects/` - Créer un projet
- `GET /projects/{id}/` - Détail projet
- `PUT /projects/{id}/` - Modifier projet
- `DELETE /projects/{id}/` - Supprimer projet
- `POST /projects/{id}/parcels/` - Import plan cadastral
- `GET /projects/{id}/parcels/` - Données parcelle
- `POST /projects/{id}/terrain/` - Diagnostic topographique
- `GET /projects/{id}/terrain/` - Résultat analyse terrain

## Budget
- `GET /projects/{id}/budget/` - Budget du projet
- `PUT /projects/{id}/budget/` - Modifier budget
- `GET /projects/{id}/budget/realtime/` - Coût temps réel
- `GET /projects/{id}/phases/` - Phases du projet
- `POST /projects/{id}/phases/` - Créer une phase
- `PUT /projects/{id}/phases/{pid}/` - Modifier phase

## Génération & Design
- `POST /designs/generate/` - Lancer génération IA
- `GET /designs/{id}/status/` - Statut génération
- `GET /designs/{id}/` - Récupérer design
- `PUT /designs/{id}/` - Sauvegarder modifications
- `POST /designs/{id}/validate/` - Valider design
- `POST /designs/{id}/elements/` - Ajouter élément
- `GET /designs/{id}/elements/` - Liste des éléments
- `PUT /designs/{id}/elements/{eid}/` - Modifier élément
- `DELETE /designs/{id}/elements/{eid}/` - Supprimer élément
- `POST /designs/{id}/simulate/` - Simulation temporelle
- `GET /designs/{id}/simulations/` - Rendus temporels

## Devis (Phase 2)
- `POST /projects/{id}/quotes/` - Générer devis
- `GET /projects/{id}/quotes/` - Liste devis
- `GET /projects/{id}/quotes/{qid}/` - Détail devis
- `PUT /projects/{id}/quotes/{qid}/` - Modifier devis
- `POST /quotes/{qid}/export-pdf/` - Export PDF
- `POST /quotes/{qid}/send/` - Envoyer par email
- `PUT /quotes/{qid}/accept/` - Accepter devis
- `PUT /quotes/{qid}/reject/` - Rejeter devis

## Entretien
- `POST /projects/{id}/care/generate/` - Générer calendrier
- `GET /projects/{id}/care/` - Calendrier entretien
- `GET /projects/{id}/care/month/{m}/` - Tâches du mois
- `PUT /care-tasks/{tid}/complete/` - Marquer tâche faite
- `GET /plants/{id}/care-guide/` - Guide entretien plante
- `GET /notifications/` - Notifications utilisateur
- `PUT /notifications/{nid}/read/` - Marquer lu
- `PUT /notifications/read-all/` - Tout marquer lu

## Végétaux
- `GET /plants/` - Liste végétaux (filtrable)
- `GET /plants/{id}/` - Détail végétal
- `GET /plants/search/` - Recherche textuelle
- `GET /plant-families/` - Familles de plantes

## Espace Pro (Phase 2)
- `GET /pro/dashboard/` - KPIs paysagiste
- `GET /pro/profile/` - Profil entreprise
- `PUT /pro/profile/` - Modifier profil
- `POST /pro/profile/submit-verification/` - Soumettre vérification
- `GET /pro/profile/public-preview/` - Aperçu public profil
- `GET /pro/pricing/categories/` - Catégories tarifaires
- `POST /pro/pricing/categories/` - Créer catégorie
- `GET /pro/clients/` - Liste clients
- `POST /pro/clients/` - Créer client
- `GET /pro/gallery/` - Galerie réalisations
- `POST /pro/gallery/` - Uploader photo
- `GET /pro/projects/` - Projets clients

## Admin (Phase 2)
- `GET /admin/dashboard/` - KPIs globaux
- `GET /admin/users/` - Liste utilisateurs
- `GET /admin/pro-profiles/` - Profils professionnels
- `POST /admin/pro-profiles/{id}/approve/` - Approuver pro
- `POST /admin/pro-profiles/{id}/reject/` - Rejeter pro
- `GET /admin/subscriptions/` - Abonnements Stripe
- `GET /admin/plants/` - Gestion végétaux
- `GET /admin/market-prices/` - Prix de référence
- `GET /admin/audit-log/` - Journal d'audit

## Webhooks
- `POST /webhooks/stripe/` - Webhooks Stripe