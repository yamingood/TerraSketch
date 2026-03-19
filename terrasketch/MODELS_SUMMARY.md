# TerraSketch - Modèles Django MVP

## ✅ Modèles Créés

### 📁 Apps.Accounts
- **User** : Modèle utilisateur personnalisé avec rôles (particular, pro, agency, admin)
- **Subscription** : Abonnements Stripe avec plans (discovery, particular, pro, agency)  
- **Organization** : Organisations pour les agences
- **OrganizationMember** : Membres d'organisation avec rôles

### 📁 Apps.Projects
- **Project** : Projet principal avec budget et statut
- **Parcel** : Parcelle avec géométrie PostGIS et données cadastrales
- **TerrainAnalysis** : Analyse topographique du terrain (pente, sol, drainage)
- **EarthworkRecommendation** : Recommandations de terrassement avec coûts

### 📁 Apps.Plants  
- **PlantFamily** : Familles de plantes
- **Plant** : Plantes complètes (caractéristiques, besoins, résistances)
- **PlantStyle** : Affinité des plantes avec les styles de jardins
- **PlantCompanion** : Associations bénéfiques/incompatibles entre plantes
- **Plant3DModel** : Modèles 3D par stade de croissance
- **PlantCareTemplate** : Modèles d'entretien par mois et climat

### 📁 Apps.Designs
- **Design** : Design IA avec versions et métadonnées de génération
- **DesignElement** : Éléments du design (plantes, structures) avec PostGIS
- **TemporalSimulation** : Simulations temporelles (3M, 6M, 12M, 24M)

### 📁 Apps.Budget
- **BudgetPlan** : Plan budgétaire principal avec répartition par catégorie  
- **ProjectPhase** : Phases de réalisation (1, 2, 3) avec planning
- **Quote** : Devis avec versions et statuts
- **QuoteLineItem** : Lignes de devis détaillées
- **MarketPrice** : Prix de référence du marché par région

## 🗄️ Fonctionnalités Clés

### PostGIS Integration
- Géométries des parcelles (POLYGON)
- Positions des éléments de design (POINT)  
- Zones de recommandations de terrassement

### JSON Fields
- Paramètres de génération IA
- Mois de floraison des plantes
- Préférences de sol et zones climatiques
- Alertes de conflit de densité végétale

### UUID Primary Keys
- Tous les modèles utilisent UUID pour la sécurité
- Support natif pour les APIs distribuées

### Auto-calculated Fields
- Surface et périmètre des parcelles
- Totaux TTC des devis  
- Taux d'utilisation du budget
- Marges de contingence

### Versioning
- Designs avec versions multiples
- Devis avec historique des versions
- Traçabilité complète des modifications

## 🔄 Relations Inter-Apps

```
User → Project → Parcel → TerrainAnalysis → EarthworkRecommendation
     → Subscription
     → Organization → OrganizationMember

Project → Design → DesignElement → Plant
       → BudgetPlan → ProjectPhase
       → Quote → QuoteLineItem

Plant → PlantFamily
      → PlantStyle  
      → PlantCompanion
      → Plant3DModel
      → PlantCareTemplate

Design → TemporalSimulation
```

## 📋 Prêt pour MVP

Les modèles couvrent l'intégralité du MVP Phase 1 :
- ✅ Authentification multi-rôles avec Stripe
- ✅ Gestion de projets et parcelles géographiques  
- ✅ Analyse terrain et recommandations terrassement
- ✅ Bibliothèque végétale complète avec 3D et entretien
- ✅ Génération IA de designs avec éléments géolocalisés
- ✅ Simulation temporelle de l'évolution des plantations
- ✅ Gestion budgétaire et devis avec phases

**Prochaines étapes :** Migrations Django + API REST + Frontend React