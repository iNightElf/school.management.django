import { create } from 'zustand';
import { api } from './api';

function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token');
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function setupAuthInterceptor(getAuthStore: () => { setState: (s: { user: null }) => void }) {
  api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          try {
            const res = await api.post('/auth/refresh/', { refresh: refreshToken });
            const { access, refresh: newRefresh } = res.data;
            setTokens(access, newRefresh || refreshToken);
            error.config.headers.Authorization = `Bearer ${access}`;
            return api(error.config);
          } catch (e) {
            if (import.meta.env.DEV) console.warn('[store] refresh token failed', e);
            getAuthStore().setState({ user: null });
            clearTokens();
          }
        } else {
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
      const res = await api.post('/auth/login/', { email, password });
      setTokens(res.data.access, res.data.refresh);
      await get().fetchSession();
    },

    fetchSession: async () => {
      if (fetching) return;
      fetching = true;
      try {
        const token = getAccessToken();
        if (!token) {
          set({ user: null, loading: false });
          return;
        }
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
      clearTokens();
      set({ user: null });
    },
  };
});
