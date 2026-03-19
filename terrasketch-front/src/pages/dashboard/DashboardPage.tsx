import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useProjectsStore } from '../../stores/projectsStore';
import { usePlantsStore } from '../../stores/plantsStore';
import { 
  Plus, 
  FolderOpen, 
  Leaf, 
  Palette, 
  TrendingUp,
  Calendar,
  User,
  Settings
} from 'lucide-react';

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { projects, loadProjects, isLoading: projectsLoading } = useProjectsStore();
  const { plants, loadPlants, isLoading: plantsLoading } = usePlantsStore();

  useEffect(() => {
    loadProjects();
    loadPlants();
  }, [loadProjects, loadPlants]);

  const activeProjects = projects.filter(p => p.status === 'in_progress' || p.status === 'draft');
  const completedProjects = projects.filter(p => p.status === 'completed');

  const stats = [
    {
      label: 'Projets actifs',
      value: activeProjects.length.toString(),
      icon: FolderOpen,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      label: 'Projets terminés',
      value: completedProjects.length.toString(),
      icon: Palette,
      color: 'text-purple-600 bg-purple-100',
    },
    {
      label: 'Plantes disponibles',
      value: plants.length.toString(),
      icon: Leaf,
      color: 'text-green-600 bg-green-100',
    },
    {
      label: 'Total projets',
      value: projects.length.toString(),
      icon: TrendingUp,
      color: 'text-yellow-600 bg-yellow-100',
    },
  ];

  const recentProjects = projects
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Welcome Section */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Bonjour {user?.first_name} 👋
              </h1>
              <p className="text-gray-600 mt-1">
                Voici un aperçu de vos projets paysagers
              </p>
            </div>
            <Link
              to="/projects/new"
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="h-5 w-5" />
              <span>Nouveau projet</span>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <div key={index} className="card">
                  <div className="flex items-center">
                    <div className={`p-3 rounded-lg ${stat.color}`}>
                      <stat.icon className="h-6 w-6" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm text-gray-600">{stat.label}</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {stat.value}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Recent Projects */}
            <div className="card">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  Projets récents
                </h2>
                <Link
                  to="/projects"
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  Voir tous
                </Link>
              </div>
              
              <div className="space-y-4">
                {recentProjects.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>Aucun projet pour le moment</p>
                    <Link
                      to="/projects/new"
                      className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      Créer votre premier projet
                    </Link>
                  </div>
                ) : (
                  recentProjects.map((project) => {
                    const getStatusInfo = (status: string) => {
                      switch (status) {
                        case 'in_progress':
                          return { label: 'En cours', class: 'bg-blue-100 text-blue-800' };
                        case 'completed':
                          return { label: 'Terminé', class: 'bg-green-100 text-green-800' };
                        case 'draft':
                          return { label: 'Brouillon', class: 'bg-yellow-100 text-yellow-800' };
                        case 'archived':
                          return { label: 'Archivé', class: 'bg-gray-100 text-gray-800' };
                        default:
                          return { label: status, class: 'bg-gray-100 text-gray-800' };
                      }
                    };

                    const statusInfo = getStatusInfo(project.status);
                    const updatedAt = new Date(project.updated_at);
                    const now = new Date();
                    const diffMs = now.getTime() - updatedAt.getTime();
                    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    
                    const getTimeAgo = () => {
                      if (diffDays === 0) {
                        if (diffHours === 0) return 'Maintenant';
                        return `${diffHours} heure${diffHours > 1 ? 's' : ''}`;
                      }
                      return `${diffDays} jour${diffDays > 1 ? 's' : ''}`;
                    };

                    return (
                      <div
                        key={project.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900">
                              {project.name}
                            </h3>
                            <div className="flex items-center space-x-4 mt-2">
                              <span className="text-sm text-gray-500">
                                Modifié il y a {getTimeAgo()}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${statusInfo.class}`}>
                                {statusInfo.label}
                              </span>
                            </div>
                            <div className="mt-3">
                              <div className="flex justify-between text-sm text-gray-600 mb-1">
                                <span>Progression</span>
                                <span>{project.progress_percentage || 0}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-primary-600 h-2 rounded-full transition-all"
                                  style={{ width: `${project.progress_percentage || 0}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Actions rapides
              </h3>
              <div className="space-y-3">
                <Link
                  to="/projects/new"
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Plus className="h-5 w-5 text-primary-600" />
                  <span className="font-medium">Nouveau projet</span>
                </Link>
                <Link
                  to="/ai-recommendations/12345678-1234-5678-9abc-123456789abc"
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Leaf className="h-5 w-5 text-green-600" />
                  <span className="font-medium">Recommandations IA</span>
                </Link>
                <Link
                  to="/plants"
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Leaf className="h-5 w-5 text-green-600" />
                  <span className="font-medium">Explorer les plantes</span>
                </Link>
                <Link
                  to="/templates"
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Palette className="h-5 w-5 text-purple-600" />
                  <span className="font-medium">Modèles de design</span>
                </Link>
              </div>
            </div>

            {/* Tips & Learning */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Conseils du jour
              </h3>
              <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                <h4 className="font-medium text-primary-900 mb-2">
                  💡 Astuce jardinage
                </h4>
                <p className="text-sm text-primary-800">
                  Plantez les vivaces au printemps ou à l'automne pour une meilleure reprise.
                  Évitez les périodes de gel !
                </p>
              </div>
            </div>

            {/* Account Status */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Mon abonnement
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Plan actuel</span>
                  <span className="font-medium text-gray-900">
                    {user?.role === 'pro' ? 'Pro' : 'Particulier'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Projets restants</span>
                  <span className="font-medium text-gray-900">7/10</span>
                </div>
                <button className="w-full mt-3 btn-primary text-sm">
                  Améliorer mon plan
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;