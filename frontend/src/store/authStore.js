import { create } from 'zustand';
import api from '../lib/api';

const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    set({ user, token: access_token, isAuthenticated: true });
  },

  register: async (email, password) => {
    const response = await api.post('/api/auth/register', { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    set({ user, token: access_token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  initFromStorage: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ user: null, token: null, isAuthenticated: false });
      return;
    }
    
    set({ token, isAuthenticated: true }); // temporarily true to allow api call
    
    try {
      const response = await api.get('/api/auth/me');
      set({ user: response.data, isAuthenticated: true });
    } catch (error) {
      localStorage.removeItem('token');
      set({ user: null, token: null, isAuthenticated: false });
    }
  }
}));

export default useAuthStore;
