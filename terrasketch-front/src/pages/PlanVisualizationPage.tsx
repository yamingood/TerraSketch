import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeftIcon, ArrowDownTrayIcon, PlusIcon } from '@heroicons/react/24/outline';
import { PlanViewer } from '../components/plan/PlanViewer';
import { PlanControls } from '../components/plan/PlanControls';
import { PlanInfo } from '../components/plan/PlanInfo';

interface Plant {
  id: string;
  nom: string;
  nom_latin: string;
  position: { x: number; y: number };
  taille_mature: { hauteur: number; largeur: number };
  type: string;
  zone_climatique: string[];
  couleur_floraison?: string;
  periode_floraison?: string[];
}

interface Zone {
  nom: string;
  type: string;
  couleur: string;
  points: Array<{ x: number; y: number }>;
}

interface Plan {
  id: string;
  nom: string;
  description: string;
  terrain: {
    dimensions: { longueur: number; largeur: number };
    exposition: string;
    type_sol: string;
  };
  plantes: Plant[];
  zones: Zone[];
  style: string;
  budget_estime: number;
  temps_entretien: string;
  created_at: string;
  version: number;
}

const PlanVisualizationPage: React.FC = () => {
  const { planId } = useParams<{ planId: string }>();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlant, setSelectedPlant] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [showGrid, setShowGrid] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  useEffect(() => {
    if (planId) {
      loadPlan(planId);
    }
  }, [planId]);

  const loadPlan = async (id: string) => {
    try {
      setLoading(true);
      // Pour le MVP, on simule des données
      const mockPlan: Plan = {
        id: id,
        nom: "Jardin Méditerranéen Modern",
        description: "Un jardin contemporain inspiré du style méditerranéen avec des plantes résistantes à la sécheresse",
        terrain: {
          dimensions: { longueur: 25, largeur: 15 },
          exposition: "Sud",
          type_sol: "Calcaire"
        },
        plantes: [
          {
            id: "1",
            nom: "Olivier",
            nom_latin: "Olea europaea",
            position: { x: 12, y: 8 },
            taille_mature: { hauteur: 8, largeur: 6 },
            type: "Arbre",
            zone_climatique: ["Méditerranéen"],
            couleur_floraison: "Blanc",
            periode_floraison: ["Avril", "Mai"]
          },
          {
            id: "2", 
            nom: "Lavande",
            nom_latin: "Lavandula angustifolia",
            position: { x: 18, y: 5 },
            taille_mature: { hauteur: 1, largeur: 1.2 },
            type: "Arbuste",
            zone_climatique: ["Méditerranéen"],
            couleur_floraison: "Violet",
            periode_floraison: ["Juin", "Juillet", "Août"]
          },
          {
            id: "3",
            nom: "Palmier Phoenix",
            nom_latin: "Phoenix canariensis",
            position: { x: 5, y: 12 },
            taille_mature: { hauteur: 12, largeur: 8 },
            type: "Arbre",
            zone_climatique: ["Tropical", "Méditerranéen"],
            couleur_floraison: "Jaune",
            periode_floraison: ["Mars", "Avril", "Mai"]
          }
        ],
        zones: [
          {
            nom: "Terrasse",
            type: "hardscape",
            couleur: "#8B5A2B",
            points: [
              { x: 0, y: 0 },
              { x: 8, y: 0 },
              { x: 8, y: 6 },
              { x: 0, y: 6 }
            ]
          },
          {
            nom: "Pelouse",
            type: "grass",
            couleur: "#4ADE80",
            points: [
              { x: 8, y: 6 },
              { x: 25, y: 6 },
              { x: 25, y: 15 },
              { x: 8, y: 15 }
            ]
          }
        ],
        style: "Méditerranéen",
        budget_estime: 2500,
        temps_entretien: "2-3h/semaine",
        created_at: new Date().toISOString(),
        version: 1
      };

      // Simulation d'un délai de chargement
      setTimeout(() => {
        setPlan(mockPlan);
        setLoading(false);
      }, 1000);

    } catch (err) {
      console.error('Erreur lors du chargement du plan:', err);
      setError("Impossible de charger le plan");
      setLoading(false);
    }
  };

  const handleExportPNG = async () => {
    try {
      // TODO: Implémenter l'export PNG réel
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (canvas) {
        const link = document.createElement('a');
        link.download = `${plan?.nom || 'plan'}.png`;
        link.href = canvas.toDataURL();
        link.click();
      }
    } catch (err) {
      console.error('Erreur export PNG:', err);
    }
  };

  const handleCreateVariant = () => {
    // TODO: Implémenter création variante
    console.log('Créer une variante du plan');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Chargement du plan...</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Erreur</h3>
          <p className="text-gray-600 mb-4">{error || "Plan non trouvé"}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700"
          >
            Retour au tableau de bord
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ChevronLeftIcon className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{plan.nom}</h1>
                <p className="text-sm text-gray-500">Version {plan.version}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleCreateVariant}
                className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Variante</span>
              </button>
              
              <button
                onClick={handleExportPNG}
                className="flex items-center space-x-2 px-3 py-2 bg-emerald-600 text-white rounded-md text-sm font-medium hover:bg-emerald-700"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Exporter PNG</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Zone de visualisation principale */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <PlanControls
                viewMode={viewMode}
                setViewMode={setViewMode}
                showGrid={showGrid}
                setShowGrid={setShowGrid}
                showLabels={showLabels}
                setShowLabels={setShowLabels}
              />
              
              <div className="p-4">
                <PlanViewer
                  plan={plan}
                  selectedPlant={selectedPlant}
                  onPlantSelect={setSelectedPlant}
                  viewMode={viewMode}
                  showGrid={showGrid}
                  showLabels={showLabels}
                />
              </div>
            </div>
          </div>

          {/* Panneau d'informations */}
          <div className="lg:col-span-1">
            <PlanInfo 
              plan={plan}
              selectedPlant={selectedPlant ? plan.plantes.find(p => p.id === selectedPlant) || null : null}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlanVisualizationPage;