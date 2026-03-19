import { api } from '../lib/api';
import type { AIRecommendationRequest, AIRecommendationResponse } from '../lib/types';

export const aiApi = {
  // Obtenir des recommandations IA pour un projet
  getPlantRecommendations: async (
    projectId: string,
    criteria: {
      sun_exposure?: string;
      soil_type?: string;
      climate_zone?: string;
      style?: string;
    }
  ): Promise<AIRecommendationResponse> => {
    const params = new URLSearchParams();
    
    Object.entries(criteria).forEach(([key, value]) => {
      if (value) {
        params.append(key, value);
      }
    });
    
    const response = await api.get(
      `/plants/recommendations/${projectId}/?${params.toString()}`
    );
    return response.data;
  },

  // Générer des recommandations basées sur une description de projet
  generateProjectRecommendations: async (
    projectId: string,
    request: AIRecommendationRequest
  ): Promise<AIRecommendationResponse> => {
    const response = await api.post(
      `/ai/project-recommendations/${projectId}/`,
      request
    );
    return response.data;
  },

  // Obtenir des conseils d'entretien personnalisés
  getMaintenanceAdvice: async (
    projectId: string,
    plantIds: string[]
  ): Promise<{
    advice: string[];
    calendar: { month: number; tasks: string[] }[];
  }> => {
    const response = await api.post(`/ai/maintenance-advice/${projectId}/`, {
      plant_ids: plantIds
    });
    return response.data;
  }
};

export default aiApi;