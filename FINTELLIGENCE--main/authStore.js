import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,

      login: (userData, token) => {
        // Decode JWT to get role if not explicitly provided
        const payload = JSON.parse(atob(token.split('.')[1]));
        set({ 
          user: userData, 
          token: token, 
          role: payload.role || userData.role, 
          isAuthenticated: true 
        });
        localStorage.setItem('token', token);
      },

      logout: () => {
        set({ user: null, token: null, role: null, isAuthenticated: false });
        localStorage.removeItem('token');
      },

      checkAuth: () => {
        const token = localStorage.getItem('token');
        if (token) {
          // Simple validation logic or refresh token call
        }
      }
    }),
    { name: 'fintelligence-auth' }
  )
);