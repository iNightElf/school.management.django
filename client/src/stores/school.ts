import { create } from 'zustand';
import { api, dedupedFetch } from './api';
import type {
  Student, Teacher, Staff, Transaction, SchoolClass, Subject,
  FeeSchedule, SchoolSettings, AcademicYear,
  OpeningBalanceHistory, Book, Result,
  Alert, Intervention, ParentCommunication, TeacherWeeklyReport,
  ClassTest, CoordinatorTask, CoordinationDashboard, SubjectAverage,
} from '../lib/types';

const CACHE_TTL = 60_000;

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
  fetchFeeSchedules: (force?: boolean) => Promise<void>;
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
  fetchAcademicYears: (force?: boolean) => Promise<void>;
  classResults: Record<string, Result[]>;
  fetchClassResults: (classId: string, session: string, term?: string) => Promise<void>;
  expenseCategories: string[];
  fetchExpenseCategories: () => Promise<void>;

  // Coordination Hub
  alerts: Alert[];
  interventions: Intervention[];
  parentCommunications: ParentCommunication[];
  weeklyReports: TeacherWeeklyReport[];
  classTests: ClassTest[];
  coordinatorTasks: CoordinatorTask[];
  coordinationDashboard: CoordinationDashboard | null;
  subjectAverages: SubjectAverage[];
  fetchAlerts: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createAlert: (data: Record<string, unknown>) => Promise<void>;
  resolveAlert: (id: string) => Promise<void>;
  fetchInterventions: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createIntervention: (data: Record<string, unknown>) => Promise<void>;
  fetchParentCommunications: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createParentCommunication: (data: Record<string, unknown>) => Promise<void>;
  fetchWeeklyReports: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createWeeklyReport: (data: Record<string, unknown>) => Promise<void>;
  submitWeeklyReport: (id: string) => Promise<void>;
  fetchClassTests: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createClassTest: (data: Record<string, unknown>) => Promise<void>;
  bulkMarks: (testId: string, marks: Array<{ studentId: string; marksObtained: number }>) => Promise<void>;
  fetchCoordinatorTasks: (params?: Record<string, string>, force?: boolean) => Promise<void>;
  createCoordinatorTask: (data: Record<string, unknown>) => Promise<void>;
  completeCoordinatorTask: (id: string) => Promise<void>;
  fetchCoordinationDashboard: (force?: boolean) => Promise<void>;
  fetchSubjectAverages: (classId: string, term: string) => Promise<SubjectAverage[]>;
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

  // Coordination Hub state
  alerts: [],
  interventions: [],
  parentCommunications: [],
  weeklyReports: [],
  classTests: [],
  coordinatorTasks: [],
  coordinationDashboard: null,
  subjectAverages: [],

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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store] fetchDashboardCounts failed", e); }
  },

  fetchClasses: async (force) => {
    if (!force && get().classes.length > 0) return;
    set((s) => ({ loading: { ...s.loading, classes: true } }));
    try {
      const res = await api.get('/classes/');
      set({ classes: res.data.results || res.data.data || res.data, lastFetched: Date.now() });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, books: false } })); }
  },
  fetchSubjects: async (classId: string) => {
    const key = `subjects_${classId}`;
    const now = Date.now();
    if (get().subjects.length > 0 && get().subjects[0]?.classId === classId && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get(`/classes/${classId}/subjects/`));
      set({ subjects: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
  },
  fetchFinance: async () => {
    const key = 'finance';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, finance: true } }));
    try { const res = await dedupedFetch(key, () => api.get('/finance/balances/')); set({ balances: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, transactions: false } })); }
  },

  fetchDashboardSummary: async (fiscalYear?: string) => {
    const key = `dashboardSummary_${fiscalYear || ''}`;
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get('/finance/dashboard-summary/', { params: { fiscalYear } }));
      set({ dashboardSummary: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
  },

  fetchFeeSchedules: async (force?: boolean) => {
    const key = 'feeSchedules';
    const now = Date.now();
    if (!force && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { const res = await dedupedFetch(key, () => api.get('/finance/fee-schedules/')); set({ feeSchedules: (res.data?.results || res.data || []), _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
  },
  fetchOpeningBalances: async (year) => {
    const key = `openingBalances_${year || ''}`;
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get('/finance/opening-balances/', { params: { year } }));
      set({ openingBalances: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
  },
  revertOpeningBalance: async (historyId) => {
    await api.post(`/finance/opening-balances/revert/${historyId}/`);
    set((s) => {
      const newFetchedAt = { ...s._fetchedAt };
      for (const key of Object.keys(newFetchedAt)) {
        if (key.startsWith('openingBalances_') || key.startsWith('openingBalanceHistory_')) {
          newFetchedAt[key] = 0;
        }
      }
      return { _fetchedAt: newFetchedAt };
    });
    await get().fetchOpeningBalances();
    await get().fetchOpeningBalanceHistory();
  },

  fetchSettings: async () => {
    const key = 'settings';
    const now = Date.now();
    if (now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try { const res = await dedupedFetch(key, () => api.get('/settings/')); set({ settings: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    await get().fetchClasses(true);
  },
  reorderClasses: async (orderedIds: string[]) => {
    await api.put('/classes/reorder/', { orderedIds });
    await get().fetchClasses(true);
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

  fetchAcademicYears: async (force?: boolean) => {
    const key = 'academicYears';
    const now = Date.now();
    if (!force && get().academicYears.length > 0 && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, academicYears: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/academic-years/'));
      set({ academicYears: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, classResults: false } })); }
  },
  fetchExpenseCategories: async () => {
    const key = 'expenseCategories';
    const now = Date.now();
    if (get().expenseCategories.length > 0 && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, expenseCategories: true } }));
    try { const res = await dedupedFetch(key, () => api.get('/categories/?type=EXPENSE')); set({ expenseCategories: (res.data?.results || res.data || []).map((c: { name: string }) => c.name), _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } }); } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
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

  fetchTodayQuiz: async () => {
    try {
      const res = await dedupedFetch('todayQuiz', () => api.get('/engagement/quiz/today/'));
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return null; }
  },
  fetchTodayRiddle: async () => {
    try {
      const res = await dedupedFetch('todayRiddle', () => api.get('/engagement/riddle/today/'));
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return null; }
  },
  fetchTodayTips: async () => {
    try {
      const res = await dedupedFetch('todayTips', () => api.get('/engagement/tips/today/'));
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return []; }
  },
  fetchActiveChallenge: async () => {
    try {
      const res = await dedupedFetch('activeChallenge', () => api.get('/engagement/challenges/active/'));
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return []; }
  },
  fetchMyStreak: async () => {
    try {
      const res = await dedupedFetch('myStreak', () => api.get('/engagement/streak/me/'));
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return null; }
  },
  fetchMoodHistory: async (days = 30) => {
    try {
      const res = await api.get('/engagement/mood/history/', { params: { days } });
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return []; }
  },
  fetchLessonPlans: async (dateStr?: string) => {
    try {
      const params: any = {};
      if (dateStr) params.date = dateStr;
      const res = await api.get('/engagement/lesson-plans/', { params });
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return []; }
  },

  // ── Coordination Hub actions ──
  fetchAlerts: async (params, force) => {
    const key = 'alerts';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, alerts: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/alerts/', { params: { limit: '2000', ...params } }));
      set({ alerts: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, alerts: false } })); }
  },
  createAlert: async (data) => {
    await api.post('/coordination/alerts/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, alerts: 0 } }));
    await get().fetchAlerts(undefined, true);
  },
  resolveAlert: async (id) => {
    await api.post(`/coordination/alerts/${id}/resolve/`);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, alerts: 0 } }));
    await get().fetchAlerts(undefined, true);
  },

  fetchInterventions: async (params, force) => {
    const key = 'interventions';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, interventions: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/interventions/', { params: { limit: '2000', ...params } }));
      set({ interventions: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, interventions: false } })); }
  },
  createIntervention: async (data) => {
    await api.post('/coordination/interventions/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, interventions: 0 } }));
    await get().fetchInterventions(undefined, true);
  },

  fetchParentCommunications: async (params, force) => {
    const key = 'parentComms';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, parentComms: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/parent-communications/', { params: { limit: '2000', ...params } }));
      set({ parentCommunications: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, parentComms: false } })); }
  },
  createParentCommunication: async (data) => {
    await api.post('/coordination/parent-communications/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, parentComms: 0 } }));
    await get().fetchParentCommunications(undefined, true);
  },

  fetchWeeklyReports: async (params, force) => {
    const key = 'weeklyReports';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, weeklyReports: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/weekly-reports/', { params: { limit: '2000', ...params } }));
      set({ weeklyReports: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, weeklyReports: false } })); }
  },
  createWeeklyReport: async (data) => {
    await api.post('/coordination/weekly-reports/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, weeklyReports: 0 } }));
    await get().fetchWeeklyReports(undefined, true);
  },
  submitWeeklyReport: async (id) => {
    await api.post(`/coordination/weekly-reports/${id}/submit/`);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, weeklyReports: 0 } }));
    await get().fetchWeeklyReports(undefined, true);
  },

  fetchClassTests: async (params, force) => {
    const key = 'classTests';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, classTests: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/class-tests/', { params: { limit: '2000', ...params } }));
      set({ classTests: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, classTests: false } })); }
  },
  createClassTest: async (data) => {
    await api.post('/coordination/class-tests/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, classTests: 0 } }));
    await get().fetchClassTests(undefined, true);
  },
  bulkMarks: async (testId, marks) => {
    await api.post(`/coordination/class-tests/${testId}/bulk_marks/`, { marks });
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, classTests: 0 } }));
    await get().fetchClassTests(undefined, true);
  },

  fetchCoordinatorTasks: async (params, force) => {
    const key = 'coordinatorTasks';
    const now = Date.now();
    if (!force && !params && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    set((s) => ({ loading: { ...s.loading, coordinatorTasks: true } }));
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/coordinator-tasks/', { params: { limit: '2000', ...params } }));
      set({ coordinatorTasks: res.data.results || res.data.data || res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
    finally { set((s) => ({ loading: { ...s.loading, coordinatorTasks: false } })); }
  },
  createCoordinatorTask: async (data) => {
    await api.post('/coordination/coordinator-tasks/', data);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, coordinatorTasks: 0 } }));
    await get().fetchCoordinatorTasks(undefined, true);
  },
  completeCoordinatorTask: async (id) => {
    await api.post(`/coordination/coordinator-tasks/${id}/complete/`);
    set((s) => ({ _fetchedAt: { ...s._fetchedAt, coordinatorTasks: 0 } }));
    await get().fetchCoordinatorTasks(undefined, true);
  },

  fetchCoordinationDashboard: async (force) => {
    const key = 'coordinationDashboard';
    const now = Date.now();
    if (!force && now - (get()._fetchedAt[key] || 0) < CACHE_TTL) return;
    try {
      const res = await dedupedFetch(key, () => api.get('/coordination/dashboard/'));
      set({ coordinationDashboard: res.data, _fetchedAt: { ...get()._fetchedAt, [key]: Date.now() } });
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); }
  },

  fetchSubjectAverages: async (classId, term) => {
    try {
      const res = await api.get(`/coordination/class-tests/subject_averages/?class_id=${classId}&term=${term}`);
      set({ subjectAverages: res.data });
      return res.data;
    } catch (e) { if (import.meta.env.DEV) console.warn("[store]", e); return []; }
  },
}));
