import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  FileText, 
  CheckCircle,
  Palette,
  Calculator,
  Map,
  ArrowRight,
  X,
  Download
} from 'lucide-react';
import CadastreUpload from '../components/CadastreUpload';

interface ProjectData {
  name: string;
  file?: File;
  parcelle?: any; // Données de la parcelle cadastrale
  style: string;
  budget: string;
  location: {
    address: string;
    city: string;
    postalCode: string;
  };
}

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [projectData, setProjectData] = useState<ProjectData>({
    name: '',
    file: undefined,
    style: '',
    budget: '',
    location: {
      address: '',
      city: '',
      postalCode: ''
    }
  });

  const gardenStyles = [
    {
      id: 'contemporary',
      name: 'Contemporain',
      description: 'Lignes épurées, plantes architecturales',
      icon: '🏗️',
      preview: 'Moderne et structuré'
    },
    {
      id: 'mediterranean',
      name: 'Méditerranéen',
      description: 'Plantes résistantes, couleurs chaudes',
      icon: '🌿',
      preview: 'Lavandes, oliviers, graminées'
    },
    {
      id: 'cottage',
      name: 'Cottage Anglais',
      description: 'Ambiance romantique, floraisons généreuses',
      icon: '🌸',
      preview: 'Rosiers, vivaces, charme anglais'
    },
    {
      id: 'japanese',
      name: 'Japonais',
      description: 'Zen, équilibre, plantes symboliques',
      icon: '🎋',
      preview: 'Bambous, érables, mousse'
    },
    {
      id: 'tropical',
      name: 'Tropical',
      description: 'Feuillages luxuriants, couleurs vives',
      icon: '🌺',
      preview: 'Palmiers, bananiers, hibiscus'
    },
    {
      id: 'naturel',
      name: 'Naturel',
      description: 'Respecte l\'écosystème local',
      icon: '🦋',
      preview: 'Biodiversité, plantes locales'
    }
  ];

  const budgetOptions = [
    {
      id: 'essential',
      name: 'Essentiel',
      range: '1 000 - 3 000€',
      description: 'Aménagement basique avec plantes essentielles',
      icon: '💡'
    },
    {
      id: 'structured',
      name: 'Structuré',
      range: '3 000 - 8 000€',
      description: 'Projet équilibré avec variété de plantes',
      icon: '🎯'
    },
    {
      id: 'premium',
      name: 'Premium',
      range: '8 000 - 15 000€',
      description: 'Aménagement complet avec plantes premium',
      icon: '⭐'
    },
    {
      id: 'prestige',
      name: 'Prestige',
      range: '15 000€+',
      description: 'Jardin d\'exception, plantes rares',
      icon: '👑'
    }
  ];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.endsWith('.dxf')) {
        setProjectData(prev => ({ ...prev, file }));
        setCurrentStep(2);
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === "application/pdf" || file.name.endsWith('.dxf')) {
        setProjectData(prev => ({ ...prev, file }));
        setCurrentStep(2);
      }
    }
  };

  const handleStyleSelect = (styleId: string) => {
    setProjectData(prev => ({ ...prev, style: styleId }));
    setCurrentStep(3);
  };

  const handleBudgetSelect = (budgetId: string) => {
    setProjectData(prev => ({ ...prev, budget: budgetId }));
    setCurrentStep(4);
  };

  const handleParcellConfirmed = (parcelle: any) => {
    setProjectData(prev => ({ 
      ...prev, 
      parcelle,
      location: {
        address: parcelle.commune || '',
        city: parcelle.commune || '',
        postalCode: ''
      }
    }));
    setCurrentStep(2);
  };

  const handleSubmit = () => {
    // Ici on créerait le projet avec les données collectées
    console.log('Projet à créer:', projectData);
    navigate('/dashboard');
  };

  const downloadSampleFile = () => {
    // Simulation de téléchargement d'un fichier d'exemple
    const link = document.createElement('a');
    link.href = '/sample-cadastral-plan.pdf';
    link.download = 'exemple-plan-cadastral.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                  currentStep >= 1 ? 'bg-primary-600 text-white' : 'bg-gray-200'
                }`}>1</span>
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                  currentStep >= 2 ? 'bg-primary-600 text-white' : 'bg-gray-200'
                }`}>2</span>
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                  currentStep >= 3 ? 'bg-primary-600 text-white' : 'bg-gray-200'
                }`}>3</span>
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                  currentStep >= 4 ? 'bg-primary-600 text-white' : 'bg-gray-200'
                }`}>4</span>
              </div>
              
              <button
                onClick={() => navigate('/login')}
                className="text-sm text-gray-600 hover:text-primary-600 font-medium"
              >
                Se connecter
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        {/* Step 1: Cadastral File Upload */}
        {currentStep === 1 && (
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Commencez votre projet d'aménagement
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Importez votre plan cadastral pour obtenir des recommandations personnalisées
            </p>
            
            <CadastreUpload 
              onParcellConfirmed={handleParcellConfirmed}
              onError={(error) => console.error('Erreur upload:', error)}
              maxSizeMb={50}
            />

            {/* Skip option */}
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

        {/* Step 2: Garden Style */}
        {currentStep === 2 && (
          <div>
            <div className="text-center mb-8">
              {projectData.file && (
                <div className="inline-flex items-center bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm mb-4">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  {projectData.file.name} importé avec succès
                </div>
              )}
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Quel style de jardin vous inspire ?
              </h2>
              <p className="text-lg text-gray-600">
                Choisissez le style qui correspond à vos goûts et à votre environnement
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
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {style.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {style.description}
                  </p>
                  <p className="text-xs text-primary-600 font-medium">
                    {style.preview}
                  </p>
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
                Nous adapterons nos recommandations à votre enveloppe budgétaire
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
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
                    <span className="text-sm font-medium text-primary-600">
                      {budget.range}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {budget.name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {budget.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Project Details */}
        {currentStep === 4 && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Informations sur votre projet
              </h2>
              <p className="text-lg text-gray-600">
                Quelques détails pour finaliser votre profil projet
              </p>
            </div>

            <div className="max-w-2xl mx-auto">
              <div className="space-y-6">
                <div>
                  <label htmlFor="projectName" className="block text-sm font-medium text-gray-700 mb-2">
                    Nom du projet
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    value={projectData.name}
                    onChange={(e) => setProjectData(prev => ({ ...prev, name: e.target.value }))}
                    className="input-base"
                    placeholder="Ex: Jardin de la Villa Provençale"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                      Adresse
                    </label>
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
                    <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
                      Ville
                    </label>
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
                  <label htmlFor="postalCode" className="block text-sm font-medium text-gray-700 mb-2">
                    Code postal
                  </label>
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

                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Récapitulatif</h3>
                  <div className="space-y-2 text-sm">
                    {projectData.file && (
                      <div className="flex items-center text-gray-600">
                        <FileText className="h-4 w-4 mr-2" />
                        Plan cadastral: {projectData.file.name}
                      </div>
                    )}
                    <div className="flex items-center text-gray-600">
                      <Palette className="h-4 w-4 mr-2" />
                      Style: {gardenStyles.find(s => s.id === projectData.style)?.name}
                    </div>
                    <div className="flex items-center text-gray-600">
                      <Calculator className="h-4 w-4 mr-2" />
                      Budget: {budgetOptions.find(b => b.id === projectData.budget)?.name}
                    </div>
                  </div>
                </div>

                <div className="flex space-x-4">
                  <button
                    onClick={() => setCurrentStep(3)}
                    className="flex-1 btn-secondary"
                  >
                    Retour
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={!projectData.name}
                    className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Créer le projet
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default OnboardingPage;