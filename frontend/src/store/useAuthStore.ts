// src/store/useAuthStore.ts
import { create } from 'zustand';
import { api } from '@/lib/api';

interface AuthState {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: typeof window !== 'undefined' ? !!localStorage.getItem('access_token') : false,
  
  login: async (email: string, password: string) => {
    await api.login({ email, password });
    set({ isAuthenticated: true });
  },
  
  logout: () => {
    api.logout();
    set({ isAuthenticated: false });
  },
  
  checkAuth: () => {
    const isAuth = !!api.getToken();
    set({ isAuthenticated: isAuth });
    return isAuth;
  },
}));