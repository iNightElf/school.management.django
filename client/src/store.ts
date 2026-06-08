import { create } from 'zustand';
import axios from 'axios';
import { API_URL } from './lib/config';
import type { 
  Student, Teacher, Staff, Transaction, SchoolClass, Subject, 
  FeeSchedule, SchoolSettings, AcademicYear,
  OpeningBalanceHistory, Book, Result 
} from './lib/types';

// ── Token helpers ──

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

// ── API instance (single source of truth for all HTTP calls) ──

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

// ── Request deduplication ──
const inflight = new Map<string, Promise<unknown>>();
export function dedupedFetch<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const existing = inflight.get(key);
  if (existing) return existing as Promise<T>;
  const p = fn().finally(() => inflight.delete(key));
  inflight.set(key, p);
  return p;
}

const CACHE_TTL = 60_000; // 60 seconds

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
          const res = await axios.post(`${API_URL}/auth/refresh/`, { refresh: refreshToken });
          const { access, refresh: newRefresh } = res.data;
          setTokens(access, newRefresh || refreshToken);
          error.config.headers.Authorization = `Bearer ${access}`;
          return api(error.config);
        } catch (e) { if (import.meta.env.DEV) console.warn('[store] refresh token failed', e); useAuthStore.setState({ user: null }); clearTokens(); }
      } else {
        useAuthStore.setState({ user: null });
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth Store ──

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
}});

// ── Dark Mode ──
function getInitialDark(): boolean {
  const stored = localStorage.getItem('dark-mode');
  if (stored !== null) return stored === 'true';
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export const useDarkMode = create<{ dark: boolean; toggle: () => void }>((set, get) => ({
  dark: getInitialDark(),
  toggle: () => {
    const next = !get().dark;
    set({ dark: next });
    localStorage.setItem('dark-mode', String(next));
    document.documentElement.classList.toggle('dark', next);
  },
}));

if (useDarkMode.getState().dark) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

// ── UI Store (mode switching like old app) ──

type MainMode = null | 'idcard' | 'accessories' | 'result' | 'finance';
type IdSubMode = 'student' | 'teacher' | 'staff';

interface UIState {
  activeMode: MainMode;
  activeSubMode: IdSubMode;
  setMode: (mode: MainMode) => void;
  setIdSubMode: (sub: IdSubMode) => void;
  swipeBack: () => void;
  registerSwipeBack: (fn: () => void) => void;
}

let _swipeBackFn: (() => void) | null = null;

export const useUIStore = create<UIState>((set, get) => ({
  activeMode: null,
  activeSubMode: 'student',
  setMode: (mode) => set({ activeMode: mode }),
  setIdSubMode: (sub) => set({ activeSubMode: sub }),
  swipeBack: () => {
    const { activeMode, activeSubMode, setMode, setIdSubMode } = get();
    if (_swipeBackFn) {
      _swipeBackFn();
      _swipeBackFn = null;
      return;
    }
    if (activeMode === 'idcard' && activeSubMode !== 'student') {
      setIdSubMode('student');
    } else if (activeMode) {
      setMode(null);
    }
  },
  registerSwipeBack: (fn) => { _swipeBackFn = fn; },
}));

// ── School Store ──

interface SchoolState {
  classes: SchoolClass[];
  students: Student[];
  teachers: Teacher[];
  staff: Staff[];
  books: Book[];
  subjects: Subject[];
  transactions: Transaction[];
  balances: Record<string, number>;
  settings: SchoolSettings;
  feeSchedules: FeeSchedule[];
  openingBalances: Record<string, number>;
  openingBalancesHistory: OpeningBalanceHistory[];
  studentTotal: number;
  teacherTotal: number;
  staffTotal: number;
  bookTotal: number;
  transactionTotal: number;
  transactionPage: number;
  transactionTotalPages: number;
  lastFetched: number | null;
  _fetchedAt: Record<string, number>;
  loading: Record<string, boolean>;

  fetchDashboardCounts: () => Promise<void>;
  fetchClasses: (force?: boolean) => Promise<void>;
  fetchStudents: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  fetchTeachers: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  fetchStaff: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  fetchBooks: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  fetchSubjects: (classId: string) => Promise<void>;
  fetchFinance: () => Promise<void>;
  fetchTransactions: (params?: Record<string, string>) => Promise<void>;
  dashboardSummary: { totalIncome: number; totalDepositedToBank: number; depositRemaining: number };
  fetchDashboardSummary: (fiscalYear?: string) => Promise<void>;
  fetchFeeSchedules: () => Promise<void>;
  fetchOpeningBalances: (year?: string) => Promise<void>;
  setOpeningBalances: (year: string, balances: Record<string, number>) => Promise<void>;
  fetchOpeningBalanceHistory: (year?: string) => Promise<void>;
  revertOpeningBalance: (historyId: string) => Promise<void>;
  fetchSettings: () => Promise<void>;
  updateSettings: (data: Partial<SchoolSettings>) => Promise<void>;

  createClass: (name: string) => Promise<SchoolClass>;
  deleteClass: (id: string) => Promise<void>;
  reorderClasses: (orderedIds: string[]) => Promise<void>;

  createSubject: (classId: string, name: string, fullMarks: number) => Promise<Subject>;
  updateSubject: (id: string, data: Partial<Subject>) => Promise<void>;
  deleteSubject: (id: string) => Promise<void>;

  saveStudentResult: (studentId: string, term: string, marks: Record<string, number>, attendance?: { days: number; present: number }, comment?: string, session?: string) => Promise<void>;
  studentResultsCache: Record<string, { data: Result[]; ts: number }>;
  getStudentResults: (studentId: string, session?: string) => Promise<Result[]>;

  academicYears: AcademicYear[];
  fetchAcademicYears: () => Promise<void>;
  classResults: Record<string, Result[]>;
  fetchClassResults: (classId: string, session: string, term?: string) => Promise<void>;
  expenseCategories: string[];
  fetchExpenseCategories: () => Promise<void>;
}

export const useSchoolStore = create<SchoolState>((set, get) => ({
  classes: [],
  students: [],
  teachers: [],
  staff: [],
  books: [],
  subjects: [],
  transactions: [],
  balances: { AL_RAWA_BANK: 0, GLOBAL_FORUM_BANK: 0, CASH_IN_HAND: 0 },
  settings: { school_name: 'AL RAWA English School', address: '', phone: '', email: '', website: '' },
  feeSchedules: [],
  openingBalances: { AL_RAWA_BANK: 0, GLOBAL_FORUM_BANK: 0, CASH_IN_HAND: 0 },
  openingBalancesHistory: [],
  studentTotal: 0,
  teacherTotal: 0,
  staffTotal: 0,
  bookTotal: 0,
  transactionTotal: 0,
  transactionPage: 1,
  transactionTotalPages: 1,
  lastFetched: null,
  _fetchedAt: {},
  academicYears: [],
  classResults: {},
  studentResultsCache: {},
  expenseCategories: [],
  dashboardSummary: { totalIncome: 0, totalDepositedToBank: 0, depositRemaining: 0 },
  loading: {},

  fetchDashboardCounts: async () => {
    const key = 'dashboardCounts';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get('/dashboard-summary/'));
      set({ _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
      set({
        studentTotal: res.data.studentCount,
        teacherTotal: res.data.teacherCount,
        staffTotal: res.data.staffCount,
        bookTotal: res.data.bookCount,
      });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store] fetchDashboardCounts failed", e) }
  },

  fetchClasses: async (force) => {
    if (!force && get().classes.length > 0) return;
    set((s) => ({ loading: { ...s.loading, classes: true } }));
    try { 
      const res = await api.get('/classes/'); 
      set({ classes: res.data.results || res.data.data || res.data, lastFetched: Date.now() }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, classes: false } })); }
  },
  fetchStudents: async (params, force) => {
    if (!force && get().students.length > 0 && !params) return;
    set((s) => ({ loading: { ...s.loading, students: true } }));
    try { 
      const res = await api.get('/students/', { params: { limit: '2000', ...params } }); 
      set({ 
        students: res.data.results || res.data.data || res.data, 
        studentTotal: res.data.count ?? res.data.total ?? 0, 
        lastFetched: Date.now() 
      }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, students: false } })); }
  },
  fetchTeachers: async (params, force) => {
    if (!force && get().teachers.length > 0 && !params) return;
    set((s) => ({ loading: { ...s.loading, teachers: true } }));
    try { 
      const res = await api.get('/teachers/', { params: { limit: '2000', ...params } }); 
      set({ 
        teachers: res.data.results || res.data.data || res.data, 
        teacherTotal: res.data.count ?? res.data.total ?? 0, 
        lastFetched: Date.now() 
      }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, teachers: false } })); }
  },
  fetchStaff: async (params, force) => {
    if (!force && get().staff.length > 0 && !params) return;
    set((s) => ({ loading: { ...s.loading, staff: true } }));
    try { 
      const res = await api.get('/staff/', { params: { limit: '2000', ...params } }); 
      set({ 
        staff: res.data.results || res.data.data || res.data, 
        staffTotal: res.data.count ?? res.data.total ?? 0, 
        lastFetched: Date.now() 
      }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, staff: false } })); }
  },
  fetchBooks: async (params, force) => {
    if (!force && get().books.length > 0 && !params) return;
    set((s) => ({ loading: { ...s.loading, books: true } }));
    try { 
      const res = await api.get('/books/', { params: { limit: '2000', ...params } }); 
      set({ 
        books: res.data.results || res.data.data || res.data, 
        bookTotal: res.data.count ?? res.data.total ?? 0, 
        lastFetched: Date.now() 
      }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, books: false } })); }
  },
  fetchSubjects: async (classId: string) => {
    const key = `subjects_${classId}`;
    const now = Date.now();
    if (get().subjects.length > 0 && get().subjects[0]?.classId === classId && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { 
      const res = await dedupedFetch(key, () => api.get(`/classes/${classId}/subjects/`)); 
      set({ subjects: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },
  fetchFinance: async () => {
    const key = 'finance';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, finance: true } }));
    try { const res = await dedupedFetch(key, () => api.get('/finance/balances/')); set({ balances: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, finance: false } })); }
  },
  fetchTransactions: async (params?: Record<string, string>) => {
    const key = 'transactions';
    const now = Date.now();
    if (!params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, transactions: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/finance/transactions/', { params }));
      set({ _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
      if (Array.isArray(res.data)) {
        set({ transactions: res.data });
      } else if (res.data?.data) {
        set({ transactions: res.data.data, transactionTotal: res.data.total, transactionPage: res.data.page, transactionTotalPages: res.data.totalPages });
      } else if (res.data?.results) {
        set({ transactions: res.data.results, transactionTotal: res.data.count ?? 0 });
      }
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, transactions: false } })); }
  },

  fetchDashboardSummary: async (fiscalYear?: string) => {
    const key = `dashboardSummary_${fiscalYear || ''}`;
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get('/finance/dashboard-summary/', { params: { fiscalYear } }));
      set({ dashboardSummary: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },

  fetchFeeSchedules: async () => {
    const key = 'feeSchedules';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { const res = await dedupedFetch(key, () => api.get('/finance/fee-schedules/')); set({ feeSchedules: (res.data?.results || res.data || []), _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },
  fetchOpeningBalances: async (year) => {
    const key = `openingBalances_${year || ''}`;
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { 
      const res = await dedupedFetch(key, () => api.get('/finance/opening-balances/', { params: { year } })); 
      set({ openingBalances: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },

  setOpeningBalances: async (year, balances) => {
    const res = await api.put('/finance/opening-balances/', { year, balances });
    const key = `openingBalances_${year || ''}`;
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, [key]: 0 } }));
    await get().fetchOpeningBalances(year);
    return res.data;
  },
  fetchOpeningBalanceHistory: async (year) => {
    const key = `openingBalanceHistory_${year || ''}`;
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { 
      const res = await dedupedFetch(key, () => api.get('/finance/opening-balances/history/', { params: { year } })); 
      set({ openingBalancesHistory: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },
  revertOpeningBalance: async (historyId) => {
    await api.post(`/finance/opening-balances/revert/${historyId}/`);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, openingBalances_: 0, openingBalanceHistory_: 0 } }));
    await get().fetchOpeningBalances();
    await get().fetchOpeningBalanceHistory();
  },

  fetchSettings: async () => {
    const key = 'settings';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { const res = await dedupedFetch(key, () => api.get('/settings/')); set({ settings: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },
  updateSettings: async (data) => {
    const res = await api.put('/settings/', data);
    set((s) => ({ settings: res.data, _fetchedAt: { ...s._fetchedAt, settings: Date.now() } }));
  },

  createClass: async (name: string) => {
    const res = await api.post('/classes/', { name });
    await get().fetchClasses();
    return res.data;
  },
  deleteClass: async (id: string) => {
    await api.delete(`/classes/${id}/`);
    await get().fetchClasses();
  },
  reorderClasses: async (orderedIds: string[]) => {
    await api.put('/classes/reorder/', { orderedIds });
    await get().fetchClasses();
  },

  createSubject: async (classId: string, name: string, fullMarks: number) => {
    const res = await api.post(`/classes/${classId}/subjects/`, { name, fullMarks });
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, [`subjects_${classId}`]: 0 } }));
    await get().fetchSubjects(classId);
    return res.data;
  },
  updateSubject: async (id: string, data: Partial<Subject>) => {
    await api.put(`/subjects/${id}/`, data);
    const currentSubjects = get().subjects;
    const updated = currentSubjects.find((s) => s.id === id);
    if (updated) {
      set((s) => ({ _fetchedAt: { ...s._fetchedAt, [`subjects_${updated.classId}`]: 0 } }));
      await get().fetchSubjects(updated.classId);
    }
  },
  deleteSubject: async (id: string) => {
    const currentSubjects = get().subjects;
    const deleted = currentSubjects.find((s) => s.id === id);
    await api.delete(`/subjects/${id}/`);
    if (deleted) {
      set((s) => ({ _fetchedAt: { ...s._fetchedAt, [`subjects_${deleted.classId}`]: 0 } }));
      await get().fetchSubjects(deleted.classId);
    }
  },

  fetchAcademicYears: async () => {
    const key = 'academicYears';
    const now = Date.now();
    if (get().academicYears.length > 0 && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, academicYears: true } }));
    try { 
      const res = await dedupedFetch(key, () => api.get('/academic-years/')); 
      set({ academicYears: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, academicYears: false } })); }
  },
  fetchClassResults: async (classId: string, session: string, term?: string) => {
    const cacheKey = `${classId}-${session}${term ? '-' + term : ''}`;
    const key = `classResults_${cacheKey}`;
    const now = Date.now();
    if (get().classResults[cacheKey] && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, classResults: true } }));
    try { 
      const params: Record<string, string> = { session };
      if (term) params.term = term;
      const res = await dedupedFetch(key, () => api.get(`/classes/${classId}/results/`, { params }));
      set((s) => ({ classResults: { ...s.classResults, [cacheKey]: res.data.results || res.data.data || res.data }, _fetchedAt: { ...s._fetchedAt, [key]: Date.now() } })); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, classResults: false } })); }
  },
  fetchExpenseCategories: async () => {
    const key = 'expenseCategories';
    const now = Date.now();
    if (get().expenseCategories.length > 0 && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, expenseCategories: true } }));
    try { const res = await dedupedFetch(key, () => api.get('/categories/?type=EXPENSE')); set({ expenseCategories: (res.data?.results || res.data || []).map((c: { name: string }) => c.name), _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
    finally { set((s) => ({ loading: { ...s.loading, expenseCategories: false } })); }
  },

  saveStudentResult: async (studentId: string, term: string, marks: Record<string, number>, attendance?: { days: number; present: number }, comment?: string, session?: string) => {
    await api.post(`/students/${studentId}/results/`, { term, marks, attendance, session, ...(comment !== undefined && { comment }) });
    set((s) => {
      const next = { ...s.studentResultsCache };
      for (const key of Object.keys(next)) {
        if (key.startsWith(studentId)) delete next[key];
      }
      const fetchedAt = { ...s._fetchedAt };
      for (const key of Object.keys(fetchedAt)) {
        if (key.startsWith('classResults')) fetchedAt[key] = 0;
      }
      return { studentResultsCache: next, _fetchedAt: fetchedAt };
    });
  },
  getStudentResults: async (studentId: string, session?: string) => {
    const key = `${studentId}${session ? '-' + session : ''}`;
    const cached = get().studentResultsCache[key];
    if (cached && Date.now() - cached.ts < 30000) return cached.data;
    const params = session ? { session } : {};
    const res = await api.get(`/students/${studentId}/results/`, { params });
    const data = res.data.results || res.data.data || res.data;
    set((s) => ({ studentResultsCache: { ...s.studentResultsCache, [key]: { data, ts: Date.now() } } }));
    return data;
  },
}));

// ── User Management Store (admin) ──

interface ManagedUser {
  id: string;
  name: string;
  email: string;
  role: string;
  emailVerified: boolean;
  createdAt: string;
}

interface RoleOption {
  value: string;
  label: string;
}

interface UserManagementState {
  users: ManagedUser[];
  roles: RoleOption[];
  fetchUsers: () => Promise<void>;
  fetchRoles: () => Promise<void>;
  updateRole: (userId: string, role: string) => Promise<void>;
  deleteUser: (userId: string) => Promise<void>;
}

export const useUserManagementStore = create<UserManagementState>((set, get) => ({
  users: [],
  roles: [],

  fetchUsers: async () => {
    try { 
      const res = await api.get('/users/'); 
      set({ users: res.data.results || res.data.data || res.data }); 
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },

  fetchRoles: async () => {
    try { const res = await api.get('/users/roles/'); set({ roles: res.data }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e) }
  },
  updateRole: async (userId: string, role: string) => {
    await api.put(`/users/${userId}/role/`, { role });
    await get().fetchUsers();
  },
  deleteUser: async (userId: string) => {
    await api.delete(`/users/${userId}/`);
    await get().fetchUsers();
  },
}));
