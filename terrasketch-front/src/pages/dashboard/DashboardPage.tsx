import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Map, Plus, FileText, Settings } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
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
            
            <div className="flex items-center space-x-4">
              <button className="text-gray-600 hover:text-primary-600">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Bienvenue sur votre tableau de bord !
          </h2>
          <p className="text-gray-600">
            Votre projet a été créé avec succès. Vous pouvez maintenant créer votre premier plan d'aménagement.
          </p>
        </div>

        {/* Success Message */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mr-3">
              <FileText className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-green-800">
                Onboarding terminé avec succès
              </h3>
              <p className="text-sm text-green-600">
                Votre parcelle a été analysée et vos préférences ont été enregistrées.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <div className="card hover:shadow-md transition-shadow cursor-pointer"
               onClick={() => navigate('/plan/new')}>
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mr-4">
                <Plus className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Créer un plan
                </h3>
                <p className="text-sm text-gray-500">
                  Générer votre premier aménagement
                </p>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              Utiliser l'IA pour créer un plan d'aménagement personnalisé basé sur votre parcelle et vos préférences.
            </p>
          </div>

          <div className="card hover:shadow-md transition-shadow cursor-pointer"
               onClick={() => navigate('/onboarding')}>
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mr-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Nouveau projet
                </h3>
                <p className="text-sm text-gray-500">
                  Ajouter une autre parcelle
                </p>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              Importer un nouveau plan cadastral pour créer un autre projet d'aménagement.
            </p>
          </div>

          <div className="card hover:shadow-md transition-shadow cursor-pointer"
               onClick={() => navigate('/plan/demo-plan')}>
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mr-4">
                <Map className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Voir l'exemple
                </h3>
                <p className="text-sm text-gray-500">
                  Plan de démonstration
                </p>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              Découvrir un exemple de plan d'aménagement généré par l'IA.
            </p>
          </div>
        </div>

        {/* Recent Projects */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Projets récents
          </h3>
          <div className="bg-gray-100 rounded-lg p-8 text-center">
            <Map className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              Aucun projet pour le moment.
            </p>
            <p className="text-sm text-gray-400">
              Créez votre premier plan pour commencer !
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;