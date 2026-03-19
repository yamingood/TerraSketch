import { create } from 'zustand';
import { plantsApi } from '../api/plants';
import type { Plant, PlantSearchFilters, PlantFamily } from '../lib/types';

interface PlantsState {
  plants: Plant[];
  families: PlantFamily[];
  isLoading: boolean;
  searchResults: Plant[];
  selectedPlant: Plant | null;
  filters: PlantSearchFilters;
  
  // Actions
  loadPlants: (filters?: PlantSearchFilters) => Promise<void>;
  loadFamilies: () => Promise<void>;
  searchPlants: (searchTerm: string) => Promise<void>;
  selectPlant: (plant: Plant | null) => void;
  updateFilters: (filters: PlantSearchFilters) => void;
  clearSearch: () => void;
}

export const usePlantsStore = create<PlantsState>((set, get) => ({
  plants: [],
  families: [],
  isLoading: false,
  searchResults: [],
  selectedPlant: null,
  filters: {},

  loadPlants: async (filters?: PlantSearchFilters) => {
    set({ isLoading: true });
    try {
      const plants = await plantsApi.getPlants(filters);
      set({ plants, isLoading: false });
    } catch (error) {
      console.error('Error loading plants:', error);
      set({ isLoading: false });
    }
  },

  loadFamilies: async () => {
    try {
      const families = await plantsApi.getPlantFamilies();
      set({ families });
    } catch (error) {
      console.error('Error loading families:', error);
    }
  },

  searchPlants: async (searchTerm: string) => {
    set({ isLoading: true });
    try {
      const searchResults = await plantsApi.searchPlants(searchTerm);
      set({ searchResults, isLoading: false });
    } catch (error) {
      console.error('Error searching plants:', error);
      set({ searchResults: [], isLoading: false });
    }
  },

  selectPlant: (plant: Plant | null) => {
    set({ selectedPlant: plant });
  },

  updateFilters: (filters: PlantSearchFilters) => {
    set({ filters });
    get().loadPlants(filters);
  },

  clearSearch: () => {
    set({ searchResults: [] });
  },
}));