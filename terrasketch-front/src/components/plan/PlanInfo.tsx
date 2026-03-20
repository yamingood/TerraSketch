import React from 'react';
import { 
  InformationCircleIcon,
  MapPinIcon,
  SunIcon,
  CurrencyEuroIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

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
  style: string;
  budget_estime: number;
  temps_entretien: string;
  created_at: string;
  version: number;
}

interface PlanInfoProps {
  plan: Plan;
  selectedPlant: Plant | null;
}

export const PlanInfo: React.FC<PlanInfoProps> = ({ plan, selectedPlant }) => {
  return (
    <div className="space-y-6">
      {/* Plan Information */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center space-x-2 mb-3">
          <InformationCircleIcon className="h-5 w-5 text-emerald-600" />
          <h3 className="text-lg font-medium text-gray-900">Informations du plan</h3>
        </div>
        
        <div className="space-y-3 text-sm">
          <div>
            <span className="font-medium text-gray-700">Description:</span>
            <p className="text-gray-600 mt-1">{plan.description}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="font-medium text-gray-700">Dimensions:</span>
              <p className="text-gray-600">{plan.terrain.dimensions.longueur}m × {plan.terrain.dimensions.largeur}m</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Surface:</span>
              <p className="text-gray-600">{plan.terrain.dimensions.longueur * plan.terrain.dimensions.largeur} m²</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="font-medium text-gray-700">Exposition:</span>
              <p className="text-gray-600 flex items-center">
                <SunIcon className="h-4 w-4 mr-1" />
                {plan.terrain.exposition}
              </p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Type de sol:</span>
              <p className="text-gray-600">{plan.terrain.type_sol}</p>
            </div>
          </div>

          <div>
            <span className="font-medium text-gray-700">Style:</span>
            <p className="text-gray-600">{plan.style}</p>
          </div>

          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1 text-gray-700">
                <CurrencyEuroIcon className="h-4 w-4" />
                <span className="font-medium">Budget estimé:</span>
              </div>
              <span className="text-emerald-600 font-semibold">{plan.budget_estime}€</span>
            </div>
            
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center space-x-1 text-gray-700">
                <ClockIcon className="h-4 w-4" />
                <span className="font-medium">Entretien:</span>
              </div>
              <span className="text-gray-600">{plan.temps_entretien}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Selected Plant Information */}
      {selectedPlant ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center space-x-2 mb-3">
            <MapPinIcon className="h-5 w-5 text-emerald-600" />
            <h3 className="text-lg font-medium text-gray-900">Plante sélectionnée</h3>
          </div>
          
          <div className="space-y-3 text-sm">
            <div>
              <h4 className="font-semibold text-gray-900">{selectedPlant.nom}</h4>
              <p className="text-gray-600 italic">{selectedPlant.nom_latin}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="font-medium text-gray-700">Type:</span>
                <p className="text-gray-600">{selectedPlant.type}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Position:</span>
                <p className="text-gray-600">{selectedPlant.position.x}m, {selectedPlant.position.y}m</p>
              </div>
            </div>

            <div>
              <span className="font-medium text-gray-700">Taille mature:</span>
              <p className="text-gray-600">
                {selectedPlant.taille_mature.hauteur}m (H) × {selectedPlant.taille_mature.largeur}m (L)
              </p>
            </div>

            <div>
              <span className="font-medium text-gray-700">Zones climatiques:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {selectedPlant.zone_climatique.map((zone, index) => (
                  <span 
                    key={index}
                    className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs"
                  >
                    {zone}
                  </span>
                ))}
              </div>
            </div>

            {selectedPlant.couleur_floraison && (
              <div>
                <span className="font-medium text-gray-700">Couleur floraison:</span>
                <p className="text-gray-600">{selectedPlant.couleur_floraison}</p>
              </div>
            )}

            {selectedPlant.periode_floraison && selectedPlant.periode_floraison.length > 0 && (
              <div>
                <span className="font-medium text-gray-700">Période de floraison:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedPlant.periode_floraison.map((mois, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs"
                    >
                      {mois}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-center text-gray-500">
            <MapPinIcon className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">Cliquez sur une plante pour voir ses détails</p>
          </div>
        </div>
      )}

      {/* Plants List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-3">
          Plantes du plan ({plan.plantes.length})
        </h3>
        
        <div className="space-y-2">
          {plan.plantes.map((plant) => (
            <div 
              key={plant.id}
              className={`p-3 rounded-lg border-2 transition-colors cursor-pointer ${
                selectedPlant?.id === plant.id 
                  ? 'border-emerald-200 bg-emerald-50' 
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 text-sm">{plant.nom}</h4>
                  <p className="text-xs text-gray-600 italic">{plant.nom_latin}</p>
                </div>
                <div className="text-right text-xs text-gray-500">
                  <div>{plant.type}</div>
                  <div className="flex items-center">
                    <MapPinIcon className="h-3 w-3 mr-1" />
                    {plant.position.x}m, {plant.position.y}m
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};