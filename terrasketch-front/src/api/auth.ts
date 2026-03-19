import { api } from '../lib/api';
import type { User } from '../lib/types';

export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: string;
}

export const authApi = {
  // Connexion utilisateur
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login/', credentials);
    const data = response.data;
    
    // Stocker les tokens
    localStorage.setItem('accessToken', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    
    return data;
  },

  // Inscription utilisateur
  register: async (userData: RegisterData): Promise<AuthResponse> => {
    const response = await api.post('/auth/register/', userData);
    const data = response.data;
    
    // Stocker les tokens
    localStorage.setItem('accessToken', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    
    return data;
  },

  // Obtenir le profil utilisateur
  getProfile: async (): Promise<User> => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  // Mettre à jour le profil
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await api.patch('/auth/profile/update/', userData);
    return response.data;
  },

  // Rafraîchir le token
  refreshToken: async (refreshToken: string): Promise<{ access: string }> => {
    const response = await api.post('/auth/refresh/', { refresh: refreshToken });
    
    // Mettre à jour le token stocké
    localStorage.setItem('accessToken', response.data.access);
    
    return response.data;
  },

  // Déconnexion
  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login';
  },

  // Vérifier si l'utilisateur est connecté
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('accessToken');
  },

  // Obtenir le token d'accès
  getAccessToken: (): string | null => {
    return localStorage.getItem('accessToken');
  }
};

export default authApi;