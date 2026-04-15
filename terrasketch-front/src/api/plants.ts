import { api } from '../lib/api';
import type {
  Plant,
  PlantFamily,
  PlantSearchFilters,
  PlantRecommendationResponse,
  SearchFiltersOptions
} from '../lib/types';

export const plantsApi = {
  // Obtenir toutes les plantes avec filtres optionnels
  getPlants: async (filters?: PlantSearchFilters): Promise<Plant[]> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await api.get(`/plants/?${params.toString()}`);
    return response.data;
  },

  // Obtenir une plante par ID
  getPlant: async (id: string): Promise<Plant> => {
    const response = await api.get(`/plants/${id}/`);
    return response.data;
  },

  // Obtenir toutes les familles de plantes
  getPlantFamilies: async (): Promise<PlantFamily[]> => {
    const response = await api.get('/plants/families/');
    return response.data;
  },

  // Obtenir les options de filtres de recherche
  getSearchFilters: async (): Promise<SearchFiltersOptions> => {
    const response = await api.get('/plants/search-filters/');
    return response.data;
  },

  // Obtenir des recommandations de plantes pour un projet
  getPlantRecommendations: async (
    projectId: string, 
    criteria?: {
      sun_exposure?: string;
      soil_type?: string;
      climate_zone?: string;
      style?: string;
    }
  ): Promise<PlantRecommendationResponse> => {
    const params = new URLSearchParams();
    
    if (criteria) {
      Object.entries(criteria).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });
    }
    
    const response = await api.get(`/plants/recommendations/${projectId}/?${params.toString()}`);
    return response.data;
  },

  // Recherche de plantes par nom
  searchPlants: async (searchTerm: string): Promise<Plant[]> => {
    const response = await api.get(`/plants/?search=${encodeURIComponent(searchTerm)}`);
    return response.data;
  },

  // Filtrer les plantes par exposition solaire
  getPlantsBySunExposure: async (exposure: string): Promise<Plant[]> => {
    const response = await api.get(`/plants/?sun_exposure=${exposure}`);
    return response.data;
  },

  // Filtrer les plantes par besoins en eau
  getPlantsByWaterNeed: async (waterNeed: string): Promise<Plant[]> => {
    const response = await api.get(`/plants/?water_need=${waterNeed}`);
    return response.data;
  },

  // Filtrer les plantes par famille
  getPlantsByFamily: async (familyId: string): Promise<Plant[]> => {
    const response = await api.get(`/plants/?family=${familyId}`);
    return response.data;
  }
};

export default plantsApi;