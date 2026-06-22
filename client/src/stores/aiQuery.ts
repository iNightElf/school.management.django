import { create } from 'zustand';
import { api } from './api';

interface AIQueryResult {
  type: 'table' | 'summary' | 'clarification' | 'error';
  explanation: string;
  data: Record<string, string>[];
  columns: string[];
  confidence: number;
  meta: Record<string, unknown>;
}

interface AIQueryState {
  open: boolean;
  query: string;
  loading: boolean;
  result: AIQueryResult | null;
  error: string | null;
  setOpen: (v: boolean) => void;
  setQuery: (v: string) => void;
  submit: (q: string) => Promise<void>;
  close: () => void;
}

export const useAIQueryStore = create<AIQueryState>((set) => ({
  open: false,
  query: '',
  loading: false,
  result: null,
  error: null,
  setOpen: (v) => set({ open: v, result: null, error: null, query: '' }),
  setQuery: (v) => set({ query: v }),
  submit: async (q) => {
    set({ loading: true, result: null, error: null, query: q });
    try {
      const res = await api.post('/ai/query/', { query: q });
      set({ result: res.data as AIQueryResult, loading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Request failed';
      set({ error: msg, loading: false });
    }
  },
  close: () => set({ open: false, result: null, error: null, query: '', loading: false }),
}));
