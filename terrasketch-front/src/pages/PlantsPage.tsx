import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Leaf,
  Sun,
  Droplets,
  Thermometer,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  X,
} from 'lucide-react';
import { api } from '../api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

interface PlantFamily {
  id: string;
  name_fr: string;
  name_latin: string;
}

interface Plant {
  id: string;
  name_common_fr: string;
  name_latin: string;
  family: PlantFamily;
  type: string;
  height_adult_max_cm: number;
  sun_exposure: string;
  water_need: string;
  frost_resistance_min_c: number;
  foliage?: string;
  flowering_color?: string;
  is_drought_resistant?: boolean;
  attracts_pollinators?: boolean;
  growth_rate?: string;
  style_affinities?: { style: string; affinity_score: number }[];
}

interface PlantsResponse {
  count: number;
  results: Plant[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SUN_LABELS: Record<string, { label: string; color: string }> = {
  full_sun: { label: 'Plein soleil', color: 'text-yellow-600 bg-yellow-50' },
  partial_shade: { label: 'Mi-ombre', color: 'text-orange-600 bg-orange-50' },
  full_shade: { label: 'Ombre', color: 'text-blue-600 bg-blue-50' },
};

const WATER_LABELS: Record<string, { label: string; color: string }> = {
  low: { label: 'Faible', color: 'text-yellow-700 bg-yellow-50' },
  moderate: { label: 'Modéré', color: 'text-blue-600 bg-blue-50' },
  high: { label: 'Élevé', color: 'text-blue-800 bg-blue-100' },
};

const TYPE_LABELS: Record<string, string> = {
  tree: 'Arbre',
  shrub: 'Arbuste',
  perennial: 'Vivace',
  annual: 'Annuelle',
  grass: 'Graminée',
  climber: 'Grimpante',
  groundcover: 'Couvre-sol',
  bulb: 'Bulbe',
  aquatic: 'Aquatique',
};

const GROWTH_LABELS: Record<string, { label: string; color: string }> = {
  slow: { label: 'Lente', color: 'text-green-700 bg-green-50' },
  moderate: { label: 'Modérée', color: 'text-yellow-700 bg-yellow-50' },
  fast: { label: 'Rapide', color: 'text-red-600 bg-red-50' },
};

function Badge({ label, className }: { label: string; className: string }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${className}`}>
      {label}
    </span>
  );
}

function PlantCard({ plant, onClick }: { plant: Plant; onClick: () => void }) {
  const sun = SUN_LABELS[plant.sun_exposure];
  const water = WATER_LABELS[plant.water_need];

  return (
    <button
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:shadow-md hover:border-primary-300 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">{plant.name_common_fr}</h3>
          <p className="text-xs text-gray-500 italic">{plant.name_latin}</p>
        </div>
        {plant.type && (
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full flex-shrink-0 ml-2">
            {TYPE_LABELS[plant.type] ?? plant.type}
          </span>
        )}
      </div>

      <p className="text-xs text-gray-400 mb-3">{plant.family?.name_fr}</p>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {sun && <Badge label={sun.label} className={sun.color} />}
        {water && <Badge label={`Eau : ${water.label}`} className={water.color} />}
        {plant.is_drought_resistant && (
          <Badge label="Sec" className="text-orange-600 bg-orange-50" />
        )}
        {plant.attracts_pollinators && (
          <Badge label="Pollinisateurs" className="text-purple-600 bg-purple-50" />
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="flex items-center">
          <Thermometer className="h-3 w-3 mr-1" />
          {plant.frost_resistance_min_c}°C min
        </span>
        <span>
          {plant.height_adult_max_cm >= 100
            ? `${(plant.height_adult_max_cm / 100).toFixed(1)}m`
            : `${plant.height_adult_max_cm}cm`}
        </span>
        {plant.growth_rate && (
          <Badge
            label={GROWTH_LABELS[plant.growth_rate]?.label ?? plant.growth_rate}
            className={GROWTH_LABELS[plant.growth_rate]?.color ?? ''}
          />
        )}
      </div>
    </button>
  );
}

function PlantDetail({ plant, onClose }: { plant: Plant; onClose: () => void }) {
  const sun = SUN_LABELS[plant.sun_exposure];
  const water = WATER_LABELS[plant.water_need];

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{plant.name_common_fr}</h2>
              <p className="text-sm text-gray-500 italic">{plant.name_latin}</p>
              <p className="text-sm text-gray-400 mt-1">{plant.family?.name_fr} · {plant.family?.name_latin}</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center text-gray-500 text-xs mb-1">
                <Sun className="h-3 w-3 mr-1" /> Exposition
              </div>
              <p className="font-medium text-sm">{sun?.label ?? plant.sun_exposure}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center text-gray-500 text-xs mb-1">
                <Droplets className="h-3 w-3 mr-1" /> Besoin en eau
              </div>
              <p className="font-medium text-sm">{water?.label ?? plant.water_need}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center text-gray-500 text-xs mb-1">
                <Thermometer className="h-3 w-3 mr-1" /> Rusticité
              </div>
              <p className="font-medium text-sm">{plant.frost_resistance_min_c}°C minimum</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center text-gray-500 text-xs mb-1">
                <Leaf className="h-3 w-3 mr-1" /> Hauteur adulte
              </div>
              <p className="font-medium text-sm">
                {plant.height_adult_max_cm >= 100
                  ? `${(plant.height_adult_max_cm / 100).toFixed(1)} m`
                  : `${plant.height_adult_max_cm} cm`}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mb-5">
            {plant.type && (
              <Badge label={TYPE_LABELS[plant.type] ?? plant.type} className="text-gray-700 bg-gray-100" />
            )}
            {plant.foliage && (
              <Badge
                label={plant.foliage === 'evergreen' ? 'Persistant' : plant.foliage === 'deciduous' ? 'Caduc' : 'Semi-persistant'}
                className="text-green-700 bg-green-50"
              />
            )}
            {plant.is_drought_resistant && (
              <Badge label="Résistant à la sécheresse" className="text-orange-600 bg-orange-50" />
            )}
            {plant.attracts_pollinators && (
              <Badge label="Attire les pollinisateurs" className="text-purple-600 bg-purple-50" />
            )}
            {plant.growth_rate && (
              <Badge
                label={`Croissance ${GROWTH_LABELS[plant.growth_rate]?.label?.toLowerCase() ?? plant.growth_rate}`}
                className={GROWTH_LABELS[plant.growth_rate]?.color ?? ''}
              />
            )}
          </div>

          {plant.flowering_color && (
            <div className="mb-4">
              <p className="text-xs text-gray-500 mb-1">Floraison</p>
              <p className="text-sm font-medium capitalize">{plant.flowering_color}</p>
            </div>
          )}

          {plant.style_affinities && plant.style_affinities.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">Styles recommandés</p>
              <div className="flex flex-wrap gap-2">
                {plant.style_affinities
                  .sort((a, b) => b.affinity_score - a.affinity_score)
                  .slice(0, 4)
                  .map((sa) => (
                    <span key={sa.style} className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full">
                      {sa.style} ({sa.affinity_score}/10)
                    </span>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Page principale ──────────────────────────────────────────────────────────

const PlantsPage: React.FC = () => {
  const navigate = useNavigate();
  const [plants, setPlants] = useState<Plant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPlant, setSelectedPlant] = useState<Plant | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterSun, setFilterSun] = useState('');
  const [filterWater, setFilterWater] = useState('');

  const fetchPlants = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (filterType) params.set('type', filterType);
      if (filterSun) params.set('sun_exposure', filterSun);
      if (filterWater) params.set('water_need', filterWater);

      const qs = params.toString();
      const data = await api.get<PlantsResponse | Plant[]>(`/plants/${qs ? '?' + qs : ''}`);

      // L'API peut retourner soit une liste soit un objet paginé
      if (Array.isArray(data)) {
        setPlants(data);
        setTotal(data.length);
      } else {
        const paginated = data as PlantsResponse;
        setPlants(paginated.results ?? []);
        setTotal(paginated.count ?? 0);
      }
    } catch (err: any) {
      setError(err.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [search, filterType, filterSun, filterWater]);

  useEffect(() => {
    const timer = setTimeout(fetchPlants, 300);
    return () => clearTimeout(timer);
  }, [fetchPlants]);

  const activeFiltersCount = [filterType, filterSun, filterWater].filter(Boolean).length;

  const clearFilters = () => {
    setFilterType('');
    setFilterSun('');
    setFilterWater('');
    setSearch('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-500 hover:text-gray-700"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div className="flex items-center space-x-2">
                <Leaf className="h-5 w-5 text-primary-600" />
                <h1 className="text-lg font-bold text-gray-900">Catalogue des plantes</h1>
              </div>
              <span className="text-sm text-gray-500">{total} espèces</span>
            </div>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center space-x-2 text-sm font-medium px-3 py-2 rounded-lg border transition-colors ${
                activeFiltersCount > 0
                  ? 'border-primary-500 text-primary-600 bg-primary-50'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>Filtres {activeFiltersCount > 0 && `(${activeFiltersCount})`}</span>
              {showFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>

          {/* Barre de recherche */}
          <div className="mt-3 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher une plante (nom français ou latin)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Filtres avancés */}
          {showFilters && (
            <div className="mt-3 flex flex-wrap gap-3 pb-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Tous les types</option>
                {Object.entries(TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>

              <select
                value={filterSun}
                onChange={(e) => setFilterSun(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Toutes expositions</option>
                <option value="full_sun">Plein soleil</option>
                <option value="partial_shade">Mi-ombre</option>
                <option value="full_shade">Ombre</option>
              </select>

              <select
                value={filterWater}
                onChange={(e) => setFilterWater(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Tous besoins en eau</option>
                <option value="low">Faible</option>
                <option value="moderate">Modéré</option>
                <option value="high">Élevé</option>
              </select>

              {activeFiltersCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-red-600 hover:text-red-700 flex items-center space-x-1"
                >
                  <X className="h-4 w-4" />
                  <span>Effacer</span>
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Contenu */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4" />
                <div className="h-3 bg-gray-200 rounded w-1/3 mb-3" />
                <div className="flex gap-2">
                  <div className="h-5 bg-gray-200 rounded-full w-16" />
                  <div className="h-5 bg-gray-200 rounded-full w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : plants.length === 0 ? (
          <div className="text-center py-16">
            <Leaf className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Aucune plante trouvée</p>
            <p className="text-gray-400 text-sm mt-1">Modifiez vos filtres ou votre recherche</p>
            {activeFiltersCount > 0 && (
              <button onClick={clearFilters} className="mt-4 text-sm text-primary-600 hover:text-primary-700 underline">
                Effacer tous les filtres
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {plants.map((plant) => (
              <PlantCard
                key={plant.id}
                plant={plant}
                onClick={() => setSelectedPlant(plant)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Modal détail */}
      {selectedPlant && (
        <PlantDetail plant={selectedPlant} onClose={() => setSelectedPlant(null)} />
      )}
    </div>
  );
};

export default PlantsPage;
