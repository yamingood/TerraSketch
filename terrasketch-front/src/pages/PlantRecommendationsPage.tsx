import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { aiApi } from '../api/ai';
import { usePlantsStore } from '../stores/plantsStore';
import { Loader2, Leaf, Sun, Droplets, Thermometer, Calendar } from 'lucide-react';

interface RecommendationCriteria {
  sun_exposure: string;
  soil_type: string;
  climate_zone: string;
  style: string;
}

const PlantRecommendationsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { plants: _plants } = usePlantsStore();
  
  const [criteria, setCriteria] = useState<RecommendationCriteria>({
    sun_exposure: 'partial_shade',
    soil_type: 'loam',
    climate_zone: '8',
    style: 'contemporary'
  });
  
  const [recommendations, setRecommendations] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const getRecommendations = async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const result = await aiApi.getPlantRecommendations(projectId, criteria);
      setRecommendations(result);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erreur lors de la génération des recommandations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      getRecommendations();
    }
  }, [projectId]);

  const handleCriteriaChange = (field: keyof RecommendationCriteria, value: string) => {
    setCriteria(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getSunExposureIcon = (exposure: string) => {
    switch (exposure) {
      case 'full_sun':
        return <Sun className="h-5 w-5 text-yellow-500" />;
      case 'partial_shade':
        return <Sun className="h-5 w-5 text-orange-500" />;
      case 'full_shade':
        return <Sun className="h-5 w-5 text-gray-500" />;
      default:
        return <Sun className="h-5 w-5" />;
    }
  };

  const getWaterNeedIcon = (need: string) => {
    const color = need === 'high' ? 'text-blue-600' : need === 'moderate' ? 'text-blue-400' : 'text-blue-300';
    return <Droplets className={`h-5 w-5 ${color}`} />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Recommandations IA de plantes
          </h1>
          <p className="text-gray-600 mt-2">
            Obtenez des recommandations personnalisées grâce à l'intelligence artificielle
          </p>
        </div>

        {/* Formulaire des critères */}
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Critères de recommandation
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exposition solaire
              </label>
              <select
                value={criteria.sun_exposure}
                onChange={(e) => handleCriteriaChange('sun_exposure', e.target.value)}
                className="input-base"
              >
                <option value="full_sun">Plein soleil</option>
                <option value="partial_shade">Mi-ombre</option>
                <option value="full_shade">Ombre complète</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type de sol
              </label>
              <select
                value={criteria.soil_type}
                onChange={(e) => handleCriteriaChange('soil_type', e.target.value)}
                className="input-base"
              >
                <option value="clay">Argileux</option>
                <option value="loam">Limoneux</option>
                <option value="sand">Sableux</option>
                <option value="rocky">Rocheux</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zone climatique
              </label>
              <select
                value={criteria.climate_zone}
                onChange={(e) => handleCriteriaChange('climate_zone', e.target.value)}
                className="input-base"
              >
                {Array.from({length: 11}, (_, i) => i + 1).map(zone => (
                  <option key={zone} value={zone.toString()}>
                    Zone {zone}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Style souhaité
              </label>
              <select
                value={criteria.style}
                onChange={(e) => handleCriteriaChange('style', e.target.value)}
                className="input-base"
              >
                <option value="contemporary">Contemporain</option>
                <option value="mediterranean">Méditerranéen</option>
                <option value="cottage">Cottage anglais</option>
                <option value="japanese">Japonais</option>
                <option value="tropical">Tropical</option>
                <option value="desert">Désertique</option>
              </select>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={getRecommendations}
              disabled={loading}
              className="btn-primary flex items-center space-x-2"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Leaf className="h-5 w-5" />
              )}
              <span>
                {loading ? 'Génération en cours...' : 'Obtenir des recommandations'}
              </span>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8">
            {error}
          </div>
        )}

        {recommendations && (
          <div className="space-y-8">
            {/* Concept global */}
            {recommendations.overall_concept && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Concept général
                </h2>
                <p className="text-gray-700">{recommendations.overall_concept}</p>
              </div>
            )}

            {/* Principes de design */}
            {recommendations.design_principles && recommendations.design_principles.length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Principes de design
                </h2>
                <ul className="space-y-2">
                  {recommendations.design_principles.map((principle: string, index: number) => (
                    <li key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-primary-600 rounded-full" />
                      <span className="text-gray-700">{principle}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommandations de plantes */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Plantes recommandées ({recommendations.recommendations?.length || 0})
              </h2>
              
              {recommendations.recommendations && recommendations.recommendations.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {recommendations.recommendations.map((rec: any, index: number) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-16 h-16 bg-green-100 rounded-lg flex items-center justify-center">
                            <Leaf className="h-8 w-8 text-green-600" />
                          </div>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-gray-900">
                            {rec.plant?.name_common_fr}
                          </h3>
                          <p className="text-sm text-gray-500 italic mb-2">
                            {rec.plant?.name_latin}
                          </p>
                          
                          <div className="flex items-center space-x-4 mb-3">
                            <div className="flex items-center space-x-1">
                              {getSunExposureIcon(rec.plant?.sun_exposure)}
                              <span className="text-xs text-gray-600">
                                {rec.plant?.sun_exposure}
                              </span>
                            </div>
                            
                            <div className="flex items-center space-x-1">
                              {getWaterNeedIcon(rec.plant?.water_need)}
                              <span className="text-xs text-gray-600">
                                {rec.plant?.water_need}
                              </span>
                            </div>
                            
                            <div className="flex items-center space-x-1">
                              <Thermometer className="h-4 w-4 text-gray-500" />
                              <span className="text-xs text-gray-600">
                                {rec.plant?.height_adult_max_cm}cm
                              </span>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            {rec.reasoning && (
                              <div>
                                <span className="text-xs font-medium text-gray-700">Pourquoi cette plante :</span>
                                <p className="text-sm text-gray-600">{rec.reasoning}</p>
                              </div>
                            )}
                            
                            {rec.placement_suggestion && (
                              <div>
                                <span className="text-xs font-medium text-gray-700">Placement :</span>
                                <p className="text-sm text-gray-600">{rec.placement_suggestion}</p>
                              </div>
                            )}
                            
                            {rec.maintenance_tips && (
                              <div>
                                <span className="text-xs font-medium text-gray-700">Entretien :</span>
                                <p className="text-sm text-gray-600">{rec.maintenance_tips}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  Aucune recommandation trouvée pour ces critères
                </p>
              )}
            </div>

            {/* Calendrier d'entretien */}
            {recommendations.maintenance_calendar && recommendations.maintenance_calendar.length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">
                  Calendrier d'entretien
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recommendations.maintenance_calendar.map((month: any, index: number) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center space-x-2 mb-3">
                        <Calendar className="h-5 w-5 text-primary-600" />
                        <h3 className="font-medium text-gray-900">
                          {new Date(2024, month.month - 1).toLocaleDateString('fr-FR', { month: 'long' })}
                        </h3>
                      </div>
                      
                      <ul className="space-y-1">
                        {month.tasks.map((task: string, taskIndex: number) => (
                          <li key={taskIndex} className="text-sm text-gray-600">
                            • {task}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlantRecommendationsPage;