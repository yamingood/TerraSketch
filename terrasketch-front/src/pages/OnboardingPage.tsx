import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  Palette,
  Calculator,
  Map,
  ArrowRight,
  FileText,
  Loader2,
  Leaf,
} from 'lucide-react';
import CadastreUpload from '../components/CadastreUpload';
import { api } from '../api/client';

interface ProjectData {
  name: string;
  parcelle?: any;
  style: string;
  budget: string;
  maintenance: string;
  location: {
    address: string;
    city: string;
    postalCode: string;
  };
}

const STEPS = [
  { label: 'Parcelle', icon: Map },
  { label: 'Style', icon: Palette },
  { label: 'Budget', icon: Calculator },
  { label: 'Entretien', icon: Leaf },
  { label: 'Finaliser', icon: FileText },
];

const gardenStyles = [
  { id: 'contemporary', name: 'Contemporain', description: 'Lignes épurées, plantes architecturales', icon: '🏗️', preview: 'Moderne et structuré' },
  { id: 'mediterranean', name: 'Méditerranéen', description: 'Plantes résistantes, couleurs chaudes', icon: '🌿', preview: 'Lavandes, oliviers, graminées' },
  { id: 'cottage', name: 'Cottage Anglais', description: 'Ambiance romantique, floraisons généreuses', icon: '🌸', preview: 'Rosiers, vivaces, charme anglais' },
  { id: 'japanese', name: 'Japonais', description: 'Zen, équilibre, plantes symboliques', icon: '🎋', preview: 'Bambous, érables, mousse' },
  { id: 'tropical', name: 'Tropical', description: 'Feuillages luxuriants, couleurs vives', icon: '🌺', preview: 'Palmiers, bananiers, hibiscus' },
  { id: 'naturel', name: 'Naturel', description: "Respecte l'écosystème local", icon: '🦋', preview: 'Biodiversité, plantes locales' },
];

const budgetOptions = [
  { id: 'essential', name: 'Essentiel', range: '1 000 - 3 000€', description: 'Aménagement basique avec plantes essentielles', icon: '💡' },
  { id: 'structured', name: 'Structuré', range: '3 000 - 8 000€', description: 'Projet équilibré avec variété de plantes', icon: '🎯' },
  { id: 'premium', name: 'Premium', range: '8 000 - 15 000€', description: 'Aménagement complet avec plantes premium', icon: '⭐' },
  { id: 'prestige', name: 'Prestige', range: '15 000€+', description: "Jardin d'exception, plantes rares", icon: '👑' },
];

const maintenanceLevels = [
  {
    id: 'low',
    name: 'Faible',
    time: '1-2h / mois',
    description: "Jardin autonome, plantes résistantes peu gourmandes en entretien",
    icon: '😌',
    tips: ['Plantes persistantes', 'Paillage épais', 'Arrosage automatique'],
  },
  {
    id: 'medium',
    name: 'Modéré',
    time: '3-5h / mois',
    description: 'Bon équilibre entre diversité florale et temps investi',
    icon: '🌱',
    tips: ['Mix vivaces/annuelles', 'Taille saisonnière', 'Désherbage régulier'],
  },
  {
    id: 'high',
    name: 'Intensif',
    time: '6h+ / mois',
    description: "Jardin riche et fleuri toute l'année, vous aimez jardiner",
    icon: '🌺',
    tips: ['Rosiers, potager', 'Topiaires', 'Annuelles renouvelées'],
  },
];

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [projectData, setProjectData] = useState<ProjectData>({
    name: '',
    style: '',
    budget: '',
    maintenance: '',
    location: { address: '', city: '', postalCode: '' },
  });

  const handleParcellConfirmed = (parcelle: any) => {
    setProjectData(prev => ({
      ...prev,
      parcelle,
      location: {
        address: parcelle.commune || '',
        city: parcelle.commune || '',
        postalCode: '',
      },
    }));
    setCurrentStep(2);
  };

  const handleStyleSelect = (styleId: string) => {
    setProjectData(prev => ({ ...prev, style: styleId }));
    setCurrentStep(3);
  };

  const handleBudgetSelect = (budgetId: string) => {
    setProjectData(prev => ({ ...prev, budget: budgetId }));
    setCurrentStep(4);
  };

  const handleMaintenanceSelect = (level: string) => {
    setProjectData(prev => ({ ...prev, maintenance: level }));
    setCurrentStep(5);
  };

  const handleSubmit = async () => {
    if (!projectData.name.trim()) return;
    setIsSubmitting(true);
    setSubmitError('');

    try {
      const payload: Record<string, any> = {
        name: projectData.name,
        status: 'draft',
        budget_tier: projectData.budget || null,
        garden_style: projectData.style || null,
        maintenance_level: projectData.maintenance || null,
        address: projectData.location.address,
        city: projectData.location.city,
        postal_code: projectData.location.postalCode,
      };

      await api.post('/projects/', payload);
      navigate('/dashboard');
    } catch (err: any) {
      setSubmitError(err.message || 'Erreur lors de la création du projet');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Map className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">TerraSketch</h1>
            </div>

            {/* Progress steps */}
            <div className="hidden md:flex items-center space-x-1">
              {STEPS.map((step, i) => {
                const stepNum = i + 1;
                const done = currentStep > stepNum;
                const active = currentStep === stepNum;
                return (
                  <React.Fragment key={step.label}>
                    <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                      active ? 'bg-primary-100 text-primary-700' :
                      done ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      {done ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                          active ? 'bg-primary-600 text-white' : 'bg-gray-200'
                        }`}>{stepNum}</span>
                      )}
                      <span className="hidden lg:inline">{step.label}</span>
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className={`w-6 h-px ${currentStep > stepNum ? 'bg-green-400' : 'bg-gray-200'}`} />
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            <button
              onClick={() => navigate('/dashboard')}
              className="text-sm text-gray-500 hover:text-primary-600 font-medium"
            >
              Tableau de bord
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">

        {/* Step 1: Upload cadastre */}
        {currentStep === 1 && (
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Commencez votre projet d'aménagement
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Importez votre plan cadastral pour des recommandations personnalisées
            </p>
            <CadastreUpload
              onParcellConfirmed={handleParcellConfirmed}
              onError={(error) => console.error('Erreur upload:', error)}
              maxSizeMb={50}
            />
            <div className="mt-8">
              <button
                onClick={() => setCurrentStep(2)}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Continuer sans fichier (mode démo)
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Style */}
        {currentStep === 2 && (
          <div>
            <div className="text-center mb-8">
              {projectData.parcelle && (
                <div className="inline-flex items-center bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm mb-4">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Parcelle importée avec succès
                </div>
              )}
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Quel style de jardin vous inspire ?
              </h2>
              <p className="text-lg text-gray-600">
                Choisissez le style qui correspond à vos goûts
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {gardenStyles.map((style) => (
                <button
                  key={style.id}
                  onClick={() => handleStyleSelect(style.id)}
                  className={`p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${
                    projectData.style === style.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-primary-300'
                  }`}
                >
                  <div className="text-3xl mb-3">{style.icon}</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{style.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{style.description}</p>
                  <p className="text-xs text-primary-600 font-medium">{style.preview}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Budget */}
        {currentStep === 3 && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Quel est votre budget d'aménagement ?
              </h2>
              <p className="text-lg text-gray-600">
                Nous adapterons nos recommandations à votre enveloppe
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
              {budgetOptions.map((budget) => (
                <button
                  key={budget.id}
                  onClick={() => handleBudgetSelect(budget.id)}
                  className={`p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${
                    projectData.budget === budget.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-primary-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="text-2xl">{budget.icon}</div>
                    <span className="text-sm font-medium text-primary-600">{budget.range}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{budget.name}</h3>
                  <p className="text-sm text-gray-600">{budget.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Niveau d'entretien */}
        {currentStep === 4 && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Quel niveau d'entretien souhaitez-vous ?
              </h2>
              <p className="text-lg text-gray-600">
                Nous sélectionnerons des plantes adaptées à votre disponibilité
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
              {maintenanceLevels.map((level) => (
                <button
                  key={level.id}
                  onClick={() => handleMaintenanceSelect(level.id)}
                  className={`p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${
                    projectData.maintenance === level.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-primary-300'
                  }`}
                >
                  <div className="text-4xl mb-3 text-center">{level.icon}</div>
                  <h3 className="text-lg font-semibold text-gray-900 text-center mb-1">{level.name}</h3>
                  <p className="text-xs font-medium text-primary-600 text-center mb-3">{level.time}</p>
                  <p className="text-sm text-gray-600 mb-4">{level.description}</p>
                  <ul className="space-y-1">
                    {level.tips.map((tip) => (
                      <li key={tip} className="text-xs text-gray-500 flex items-center">
                        <span className="w-1.5 h-1.5 bg-primary-400 rounded-full mr-2 flex-shrink-0" />
                        {tip}
                      </li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 5: Finaliser */}
        {currentStep === 5 && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Finalisez votre projet
              </h2>
              <p className="text-lg text-gray-600">
                Donnez un nom à votre projet et précisez sa localisation
              </p>
            </div>

            <div className="max-w-2xl mx-auto space-y-6">
              <div>
                <label htmlFor="projectName" className="block text-sm font-medium text-gray-700 mb-2">
                  Nom du projet <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="projectName"
                  value={projectData.name}
                  onChange={(e) => setProjectData(prev => ({ ...prev, name: e.target.value }))}
                  className="input-base"
                  placeholder="Ex: Jardin de la Villa Provençale"
                  autoFocus
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">Adresse</label>
                  <input
                    type="text"
                    id="address"
                    value={projectData.location.address}
                    onChange={(e) => setProjectData(prev => ({
                      ...prev,
                      location: { ...prev.location, address: e.target.value }
                    }))}
                    className="input-base"
                    placeholder="123 Avenue des Fleurs"
                  />
                </div>
                <div>
                  <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">Ville</label>
                  <input
                    type="text"
                    id="city"
                    value={projectData.location.city}
                    onChange={(e) => setProjectData(prev => ({
                      ...prev,
                      location: { ...prev.location, city: e.target.value }
                    }))}
                    className="input-base"
                    placeholder="Nice"
                  />
                </div>
              </div>

              <div className="w-full md:w-1/2">
                <label htmlFor="postalCode" className="block text-sm font-medium text-gray-700 mb-2">Code postal</label>
                <input
                  type="text"
                  id="postalCode"
                  value={projectData.location.postalCode}
                  onChange={(e) => setProjectData(prev => ({
                    ...prev,
                    location: { ...prev.location, postalCode: e.target.value }
                  }))}
                  className="input-base"
                  placeholder="06000"
                />
              </div>

              {/* Récapitulatif */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Récapitulatif du projet</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center text-gray-600">
                    <Palette className="h-4 w-4 mr-2 text-primary-500" />
                    <span>Style : <strong>{gardenStyles.find(s => s.id === projectData.style)?.name || '—'}</strong></span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Calculator className="h-4 w-4 mr-2 text-primary-500" />
                    <span>Budget : <strong>{budgetOptions.find(b => b.id === projectData.budget)?.name || '—'}</strong></span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Leaf className="h-4 w-4 mr-2 text-primary-500" />
                    <span>Entretien : <strong>{maintenanceLevels.find(m => m.id === projectData.maintenance)?.name || '—'}</strong></span>
                  </div>
                  {projectData.parcelle && (
                    <div className="flex items-center text-gray-600">
                      <Map className="h-4 w-4 mr-2 text-primary-500" />
                      <span>Parcelle : <strong>importée</strong></span>
                    </div>
                  )}
                </div>
              </div>

              {submitError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {submitError}
                </div>
              )}

              <div className="flex space-x-4">
                <button
                  onClick={() => setCurrentStep(4)}
                  className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                >
                  Retour
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!projectData.name.trim() || isSubmitting}
                  className="flex-1 flex items-center justify-center py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      Créer le projet
                      <ArrowRight className="h-5 w-5 ml-2" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default OnboardingPage;
