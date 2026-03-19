import { create } from 'zustand';
import { api } from '../lib/api';
import type { Project } from '../lib/types';

interface ProjectsState {
  projects: Project[];
  selectedProject: Project | null;
  isLoading: boolean;
  
  // Actions
  loadProjects: () => Promise<void>;
  createProject: (projectData: Partial<Project>) => Promise<Project>;
  updateProject: (id: string, projectData: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  selectProject: (project: Project | null) => void;
}

export const useProjectsStore = create<ProjectsState>((set, get) => ({
  projects: [],
  selectedProject: null,
  isLoading: false,

  loadProjects: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get('/projects/');
      set({ projects: response.data, isLoading: false });
    } catch (error) {
      console.error('Error loading projects:', error);
      set({ isLoading: false });
    }
  },

  createProject: async (projectData: Partial<Project>) => {
    try {
      const response = await api.post('/projects/', projectData);
      const newProject = response.data;
      set(state => ({ 
        projects: [...state.projects, newProject] 
      }));
      return newProject;
    } catch (error) {
      console.error('Error creating project:', error);
      throw error;
    }
  },

  updateProject: async (id: string, projectData: Partial<Project>) => {
    try {
      const response = await api.patch(`/projects/${id}/`, projectData);
      const updatedProject = response.data;
      set(state => ({
        projects: state.projects.map(p => p.id === id ? updatedProject : p),
        selectedProject: state.selectedProject?.id === id ? updatedProject : state.selectedProject
      }));
      return updatedProject;
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  },

  deleteProject: async (id: string) => {
    try {
      await api.delete(`/projects/${id}/`);
      set(state => ({
        projects: state.projects.filter(p => p.id !== id),
        selectedProject: state.selectedProject?.id === id ? null : state.selectedProject
      }));
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  },

  selectProject: (project: Project | null) => {
    set({ selectedProject: project });
  },
}));