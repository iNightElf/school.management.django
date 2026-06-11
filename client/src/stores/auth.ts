import { create } from 'zustand';
import { api } from './api';

export function setupAuthInterceptor(getAuthStore: () => { setState: (s: { user: null }) => void }) {
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401 && !error.config._retry) {
        error.config._retry = true;
        try {
          await api.post('/auth/refresh/');
          return api(error.config);
        } catch (e) {
          if (import.meta.env.DEV) console.warn('[store] refresh token failed', e);
          getAuthStore().setState({ user: null });
        }
      }
      return Promise.reject(error);
    }
  );
}

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  emailVerified?: boolean;
  image: string | null;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  fetchSession: () => Promise<void>;
  logout: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => {
  let fetching = false;

  setupAuthInterceptor(() => useAuthStore);

  return {
    user: null,
    loading: true,

    login: async (email: string, password: string) => {
      await api.post('/auth/login/', { email, password });
      await get().fetchSession();
    },

    fetchSession: async () => {
      if (fetching) return;
      fetching = true;
      try {
        if (get().user) {
          set({ loading: false });
          return;
        }
        const res = await api.get('/auth/get-session/');
        set({ user: res.data?.user ?? null, loading: false });
      } catch (e) {
        if (import.meta.env.DEV) console.warn("[store] fetchSession failed", e);
        set({ user: null, loading: false });
      } finally {
        fetching = false;
      }
    },

    logout: async () => {
      await api.post('/auth/logout/').catch(() => {});
      set({ user: null });
    },
  };
});
