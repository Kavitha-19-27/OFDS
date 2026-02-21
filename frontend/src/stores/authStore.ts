import { create, StateCreator } from 'zustand';
import { persist, PersistOptions } from 'zustand/middleware';
import { User } from '../types';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (tenantName: string, email: string, password: string, fullName: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

type AuthPersist = (
  config: StateCreator<AuthState>,
  options: PersistOptions<AuthState, Pick<AuthState, 'accessToken' | 'refreshToken'>>
) => StateCreator<AuthState>;

export const useAuthStore = create<AuthState>()(
  (persist as AuthPersist)(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),

      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login({ email, password });
          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (tenantName, email, password, fullName) => {
        set({ isLoading: true });
        try {
          await authApi.register({
            tenant_name: tenantName,
            email,
            password,
            full_name: fullName,
          });
          set({ isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      signup: async (email, password, fullName) => {
        set({ isLoading: true });
        try {
          await authApi.signup({
            email,
            password,
            full_name: fullName,
          });
          set({ isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      fetchUser: async () => {
        const { accessToken } = get();
        if (!accessToken) return;
        
        set({ isLoading: true });
        try {
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          get().logout();
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state: AuthState) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
