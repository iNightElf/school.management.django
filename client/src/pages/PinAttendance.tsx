import { useState, useEffect, useRef, useCallback } from 'react';
import Toast, { toast } from '../components/Toast';
import { API_URL, TERM_NAMES } from '../lib/config';
import type { ClassAttendanceReport } from '../lib/types';

const API_BASE = API_URL.replace(/\/+$/, '');
const LS_QUEUE_KEY = 'pin_attendance_queue';
const LS_TOKEN_KEY = 'pin_auth_token';
const LS_TEACHER_KEY = 'pin_teacher';

type StatusType = 'present' | 'absent' | 'late' | 'excused' | 'unmarked';

interface Teacher { id: string; name: string; }
interface ClassInfo { id: string; name: string; }
interface Student { id: string; name: string; roll: string; }
interface QueuedRecord { school_class: string; date: string; term: string; session: string; records: Record<string, string>; timestamp: number; }

const STATUS_NAMES: Record<string, string> = { present: 'Present', absent: 'Absent', late: 'Late', excused: 'Excused' };

function todayStr() {
  return new Date().toISOString().split('T')[0];
}

async function apiGet(path: string, token: string, params?: Record<string, string>) {
  const url = new URL(`${API_BASE}${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function apiPost(path: string, token: string, body: unknown) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as any).error || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

function loadQueue(): QueuedRecord[] {
  try { return JSON.parse(localStorage.getItem(LS_QUEUE_KEY) || '[]'); } catch { return []; }
}

function saveQueue(queue: QueuedRecord[]) {
  localStorage.setItem(LS_QUEUE_KEY, JSON.stringify(queue));
}

function safeToast(msg: string, type?: 'success' | 'error' | 'info' | '') {
  try { toast(msg, type); } catch { /* toast component not mounted */ }
}

export default function PinAttendance() {
  const [screen, setScreen] = useState<'teachers' | 'pin' | 'classes' | 'attendance'>('teachers');
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherSearch, setTeacherSearch] = useState('');
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null);
  const [pin, setPin] = useState('');
  const [pinError, setPinError] = useState('');
  const [pinLoading, setPinLoading] = useState(false);
  const [token, setToken] = useState('');
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [classId, setClassId] = useState('');
  const [date, setDate] = useState(todayStr());
  const [term, setTerm] = useState('1');
  const [session, setSession] = useState(String(new Date().getFullYear()));
  const [students, setStudents] = useState<Student[]>([]);
  const [records, setRecords] = useState<Record<string, StatusType>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [offline, setOffline] = useState(!navigator.onLine);
  const [refreshKey, setRefreshKey] = useState(0);
  const [tab, setTab] = useState<'daily' | 'range'>('daily');

  const [rangeFrom, setRangeFrom] = useState(() => {
    const d = new Date(); d.setDate(1); return d.toISOString().split('T')[0];
  });
  const [rangeTo, setRangeTo] = useState(() => todayStr());
  const [rangeTerm, setRangeTerm] = useState('1');
  const [rangeReport, setRangeReport] = useState<ClassAttendanceReport | null>(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState('');

  const loadingStudentsRef = useRef(false);

  useEffect(() => {
    const savedToken = localStorage.getItem(LS_TOKEN_KEY);
    const savedTeacher = localStorage.getItem(LS_TEACHER_KEY);
    if (savedToken && savedTeacher) {
      setToken(savedToken);
      setSelectedTeacher(JSON.parse(savedTeacher));
      setScreen('classes');
    }
  }, []);

  useEffect(() => {
    const handler = () => setOffline(!navigator.onLine);
    window.addEventListener('online', handler);
    window.addEventListener('offline', handler);
    return () => {
      window.removeEventListener('online', handler);
      window.removeEventListener('offline', handler);
    };
  }, []);

  const syncQueue = useCallback(async () => {
    if (!navigator.onLine) return;
    const queue = loadQueue();
    if (queue.length === 0) return;
    const t = localStorage.getItem(LS_TOKEN_KEY);
    if (!t) return;
    for (let i = queue.length - 1; i >= 0; i--) {
      const item = queue[i];
      try {
        await apiPost('/m/attendance/batch/', t, {
          school_class: item.school_class, date: item.date, term: item.term, session: item.session, records: item.records,
        });
        queue.splice(i, 1);
      } catch { /* keep for retry */ }
    }
    saveQueue(queue);
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    if (navigator.onLine) syncQueue();
    const interval = setInterval(syncQueue, 30000);
    return () => clearInterval(interval);
  }, [syncQueue]);

  useEffect(() => {
    (async () => {
      try {
        const data: any = await (await fetch(`${API_BASE}/m/teachers/`)).json();
        const list = data.teachers || data.results || data;
        if (Array.isArray(list)) {
          setTeachers(list.map((t: any) => ({ id: t.id, name: t.name })));
        }
      } catch { /* offline */ }
    })();
  }, []);

  function goToTeacherList() {
    setScreen('teachers');
  }

  function selectTeacher(t: Teacher) {
    setSelectedTeacher(t);
    setPin('');
    setPinError('');
    setScreen('pin');
  }

  async function handlePinSubmit() {
    if (pin.length !== 6) return;
    if (!selectedTeacher) return;
    setPinLoading(true);
    setPinError('');
    try {
      const data: any = await apiPost('/m/auth/pin/', '', { teacher_id: selectedTeacher.id, pin });
      const jwt = data.access || data.token;
      setToken(jwt);
      setClasses((data.classes || []).map((c: any) => ({ id: c.id, name: c.name })));
      localStorage.setItem(LS_TOKEN_KEY, jwt);
      localStorage.setItem(LS_TEACHER_KEY, JSON.stringify(selectedTeacher));
      setScreen('classes');
    } catch (e: any) {
      setPinError(e.message || 'Invalid PIN');
    }
    setPinLoading(false);
  }

  function selectClass(c: ClassInfo) {
    setClassId(c.id);
    setScreen('attendance');
  }

  function logout() {
    localStorage.removeItem(LS_TOKEN_KEY);
    localStorage.removeItem(LS_TEACHER_KEY);
    setToken('');
    setSelectedTeacher(null);
    setClasses([]);
    setClassId('');
    setDate(todayStr());
    setStudents([]);
    setRecords({});
    setScreen('teachers');
  }

  useEffect(() => {
    if (!classId || !token) return;
    if (loadingStudentsRef.current) return;
    loadingStudentsRef.current = true;
    setLoading(true);
    apiGet('/m/students/', token, { class_id: classId })
      .then((data: any) => {
        const raw = data.students || data.results || data;
        const list = (Array.isArray(raw) ? raw : []).map((s: any) => ({
          id: s.id, name: s.name, roll: s.roll || '',
        }));
        list.sort((a: any, b: any) => String(a.roll || '').localeCompare(String(b.roll || ''), undefined, { numeric: true }));
        setStudents(list);
      })
      .catch((e) => safeToast(e.message, 'error'))
      .finally(() => { setLoading(false); loadingStudentsRef.current = false; });
  }, [classId, token]);

  useEffect(() => {
    if (!classId || !date || !token || tab !== 'daily') return;
    (async () => {
      try {
        const data: any = await apiGet('/m/attendance/', token, { class_id: classId, date });
        const list = Array.isArray(data) ? data : data.results || data;
        if (list.length > 0) {
          const map: Record<string, StatusType> = {};
          for (const r of list) map[r.student] = r.status;
          setRecords(map);
          if (list[0].term) setTerm(list[0].term);
          if (list[0].session) setSession(list[0].session);
        } else {
          setRecords({});
        }
      } catch (e) {
        setRecords({});
        if (classId) safeToast((e as any)?.message || 'Failed to load attendance', 'error');
      }
    })();
  }, [classId, date, token, tab, refreshKey]);

  function cycleStatus(studentId: string) {
    setRecords((prev) => {
      const current = prev[studentId] || 'unmarked';
      const order: StatusType[] = ['unmarked', 'present', 'absent', 'late', 'excused'];
      const idx = order.indexOf(current);
      return { ...prev, [studentId]: order[(idx + 1) % order.length] };
    });
  }

  function markAllPresent() {
    const all: Record<string, StatusType> = {};
    for (const s of students) all[s.id] = 'present';
    setRecords(all);
  }

  async function handleSave() {
    const markedRecords: Record<string, string> = {};
    Object.entries(records).forEach(([sid, status]) => {
      if (status !== 'unmarked') markedRecords[sid] = status;
    });
    if (Object.keys(markedRecords).length === 0) return;
    setSaving(true);
    const payload = { school_class: classId, date, term, session, records: markedRecords };

    try {
      if (!navigator.onLine) {
        const queue = loadQueue();
        queue.unshift({ ...payload, timestamp: Date.now() });
        saveQueue(queue);
        return;
      }

      await apiPost('/m/attendance/batch/', token, payload);
      setRefreshKey((k) => k + 1);
    } catch {
      safeToast('Server unavailable — queued for retry', 'info');
      const queue = loadQueue();
      queue.unshift({ ...payload, timestamp: Date.now() });
      saveQueue(queue);
    } finally {
      setSaving(false);
    }
  }

  async function loadRangeReport() {
    if (!classId || !rangeFrom || !rangeTo || !token) return;
    setRangeLoading(true);
    setRangeError('');
    try {
      const data: any = await apiGet('/m/attendance/class-report/', token, {
        class_id: classId, from: rangeFrom, to: rangeTo, term: rangeTerm, session,
      });
      setRangeReport(data as ClassAttendanceReport);
    } catch (e: any) {
      setRangeError(e.message || 'Failed to load report');
      setRangeReport(null);
    }
    setRangeLoading(false);
  }

  const markedCount = Object.values(records).filter(s => s !== 'unmarked').length;
  const queueCount = loadQueue().length;
  const filteredTeachers = teachers.filter((t) =>
    t.name.toLowerCase().includes(teacherSearch.toLowerCase())
  );

  if (screen === 'teachers') {
    return (
      <div className="min-h-screen bg-school-paper dark:bg-[#0f0f1a] flex flex-col">
        <div className="bg-gradient-to-br from-school-primary via-school-secondary to-school-accent2 p-5 pb-8 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3"/></svg>
            </div>
            <div>
              <h1 className="font-bold text-lg">Quick Attendance</h1>
              <p className="text-sm text-white/70">Sign in with your PIN</p>
            </div>
          </div>
          {!offline && <p className="text-xs text-white/50">Select your name to begin</p>}
          {offline && <p className="text-xs text-amber-200">Offline mode — showing cached data</p>}
        </div>
        <div className="px-4 -mt-4 mb-3">
          <input
            type="text"
            value={teacherSearch}
            onChange={(e) => setTeacherSearch(e.target.value)}
            placeholder="Search teacher name..."
            className="w-full px-4 py-2.5 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8] shadow-sm"
          />
        </div>
        <div className="flex-1 px-4 pb-4 overflow-y-auto">
          {filteredTeachers.length === 0 ? (
            <div className="text-center py-12 text-school-muted text-sm">
              {teachers.length === 0 ? 'Loading teachers...' : 'No teacher matches your search'}
            </div>
          ) : (
            <div className="space-y-1.5">
              {filteredTeachers.map((t) => (
                <button
                  key={t.id}
                  onClick={() => selectTeacher(t)}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] text-left hover:border-school-accent/50 transition-colors shadow-sm"
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-school-primary to-school-accent2 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {t.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="font-semibold text-sm text-school-primary dark:text-[#e0e0e8]">{t.name}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        <Toast />
      </div>
    );
  }

  if (screen === 'pin') {
    return (
      <div className="min-h-screen bg-school-paper dark:bg-[#0f0f1a] flex flex-col">
        <div className="bg-gradient-to-br from-school-primary via-school-secondary to-school-accent2 p-5 pb-8 text-white">
          <div className="flex items-center gap-3 mb-3">
            <button onClick={goToTeacherList} className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center hover:bg-white/25 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            </button>
            <div>
              <h1 className="font-bold text-lg">Enter PIN</h1>
              <p className="text-sm text-white/70">{selectedTeacher?.name}</p>
            </div>
          </div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-6 -mt-4">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-2xl border border-school-border dark:border-[#2a2a3e] p-8 w-full max-w-xs shadow-sm">
            <div className="flex justify-center gap-3 mb-6">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className={`w-4 h-4 rounded-full border-2 transition-all ${
                    pin.length > i
                      ? 'bg-school-accent border-school-accent'
                      : 'border-school-muted/40'
                  }`}
                />
              ))}
            </div>
            {pinError && (
              <p className="text-center text-red-500 text-sm mb-4 font-semibold">{pinError}</p>
            )}
            <div className="grid grid-cols-3 gap-3 max-w-[240px] mx-auto">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
                <button
                  key={n}
                  onClick={() => { if (pin.length < 6) setPin((p) => p + n); }}
                  className="w-full aspect-square rounded-2xl bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] font-bold text-xl hover:bg-school-border/50 dark:hover:bg-white/10 transition-colors active:scale-95"
                >
                  {n}
                </button>
              ))}
              <div />
              <button
                onClick={() => { if (pin.length < 6) setPin((p) => p + '0'); }}
                className="w-full aspect-square rounded-2xl bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] font-bold text-xl hover:bg-school-border/50 dark:hover:bg-white/10 transition-colors active:scale-95"
              >
                0
              </button>
              <button
                onClick={() => setPin((p) => p.slice(0, -1))}
                className="w-full aspect-square rounded-2xl bg-school-paper dark:bg-[#2a2a3e] text-school-muted hover:bg-school-border/50 dark:hover:bg-white/10 transition-colors active:scale-95 flex items-center justify-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM18 9l-6 6M12 9l6 6"/></svg>
              </button>
            </div>
            <button
              onClick={handlePinSubmit}
              disabled={pin.length !== 6 || pinLoading}
              className="w-full mt-6 px-4 py-3 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {pinLoading ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : 'Verify PIN'}
            </button>
          </div>
        </div>
        <Toast />
      </div>
    );
  }

  if (screen === 'classes') {
    return (
      <div className="min-h-screen bg-school-paper dark:bg-[#0f0f1a] flex flex-col">
        <div className="bg-gradient-to-br from-school-primary via-school-secondary to-school-accent2 p-5 pb-8 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5zM6 12v5c3 3 9 3 12 0v-5"/></svg>
            </div>
            <div className="flex-1">
              <h1 className="font-bold text-lg">Select Class</h1>
              <p className="text-sm text-white/70">{selectedTeacher?.name}</p>
            </div>
            <button onClick={logout} className="px-3 py-1.5 bg-white/15 rounded-lg text-xs font-semibold hover:bg-white/25 transition-colors">
              Switch
            </button>
          </div>
        </div>
        <div className="flex-1 px-4 pt-4 pb-4 -mt-4">
          {classes.length === 0 ? (
            <div className="text-center py-12 text-school-muted text-sm">No classes assigned</div>
          ) : (
            <div className="space-y-2">
              {classes.map((c) => (
                <button
                  key={c.id}
                  onClick={() => selectClass(c)}
                  className="w-full flex items-center gap-4 px-5 py-4 bg-white dark:bg-[#1a1a2e] rounded-2xl border border-school-border dark:border-[#2a2a3e] text-left hover:border-school-accent/50 transition-colors shadow-sm"
                >
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-bold text-lg">
                    {c.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-bold text-school-primary dark:text-[#e0e0e8]">{c.name}</div>
                    <div className="text-xs text-school-muted">Tap to mark attendance</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        <Toast />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-school-paper dark:bg-[#0f0f1a] flex flex-col">
      <div className="sticky top-0 z-20 bg-white dark:bg-[#1a1a2e] border-b border-school-border dark:border-[#2a2a3e]">
        <div className="flex items-center gap-3 px-4 py-3">
          <button onClick={() => setScreen('classes')} className="w-9 h-9 rounded-xl bg-school-paper dark:bg-[#2a2a3e] flex items-center justify-center hover:bg-school-border/50 dark:hover:bg-white/10 transition-colors flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          </button>
          <div className="flex-1 min-w-0">
            <div className="font-bold text-sm text-school-primary dark:text-[#e0e0e8] truncate">
              {classes.find((c) => c.id === classId)?.name || 'Attendance'}
            </div>
            <div className="text-[10px] text-school-muted font-medium">
              {selectedTeacher?.name} {!offline && queueCount > 0 && `· ${queueCount} pending`}
              {offline && '· Offline'}
            </div>
          </div>
          {offline && (
            <div className="px-2 py-1 bg-amber-100 dark:bg-amber-500/20 rounded-lg text-[10px] font-semibold text-amber-700 dark:text-amber-400">
              Offline
            </div>
          )}
        </div>
        <div className="flex px-4 pb-2 gap-1">
          <button
            onClick={() => setTab('daily')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-colors ${
              tab === 'daily' ? 'bg-school-accent text-white shadow-sm' : 'bg-school-paper dark:bg-[#2a2a3e] text-school-muted'
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => setTab('range')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-colors ${
              tab === 'range' ? 'bg-school-accent text-white shadow-sm' : 'bg-school-paper dark:bg-[#2a2a3e] text-school-muted'
            }`}
          >
            Range Report
          </button>
        </div>
      </div>

      <div className="flex-1 px-4 pt-3 pb-6 overflow-y-auto space-y-3 max-w-xl mx-auto w-full">
        {tab === 'daily' ? (
          <>
            <div className="grid grid-cols-3 gap-2">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8] col-span-2"
              />
              <select value={term} onChange={(e) => setTerm(e.target.value)} className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]">
                {Object.entries(TERM_NAMES).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <input
              type="number"
              value={session}
              onChange={(e) => setSession(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
              placeholder="Session"
            />

            {students.length > 0 && (
              <div className="flex items-center justify-between">
                <button onClick={markAllPresent} className="px-3 py-1.5 border border-school-border rounded-xl text-xs font-semibold text-school-primary dark:text-[#e0e0e8] hover:bg-school-paper dark:hover:bg-white/5 transition-colors flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5"/></svg>
                  All Present
                </button>
                <span className="text-xs text-school-muted">{markedCount}/{students.length} marked</span>
              </div>
            )}

            {queueCount > 0 && (
              <div className="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl px-4 py-2 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span className="text-xs text-amber-700 dark:text-amber-400 font-medium">
                  {queueCount} record{queueCount > 1 ? 's' : ''} pending sync
                </span>
                {!offline && (
                  <button onClick={syncQueue} className="px-2 py-1 bg-amber-500 text-white text-[10px] font-bold rounded-lg hover:bg-amber-600 transition-colors">
                    Sync Now
                  </button>
                )}
                <button onClick={() => { saveQueue([]); setRefreshKey((k) => k + 1); safeToast('Queue cleared', 'info'); }} className="px-2 py-1 border border-amber-300 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 text-[10px] font-bold rounded-lg hover:bg-amber-50 dark:hover:bg-amber-500/10 transition-colors">
                  Clear
                </button>
              </div>
            )}

            {loading ? (
              <div className="flex justify-center py-12">
                <div className="w-7 h-7 border-3 border-school-primary/20 border-t-school-primary rounded-full animate-spin" />
              </div>
            ) : students.length === 0 ? (
              <div className="text-center py-12 text-school-muted text-sm">
                {classId ? 'No students in this class' : 'Select a class'}
              </div>
            ) : (
              <div className="bg-white dark:bg-[#1a1a2e] rounded-2xl border border-school-border dark:border-[#2a2a3e] divide-y divide-school-border/50 dark:divide-[#2a2a3e] overflow-hidden">
                {students.map((s) => {
                  const status = records[s.id] || 'unmarked';
                  const bgColor = status === 'present' ? 'bg-green-50 dark:bg-green-500/10'
                    : status === 'absent' ? 'bg-red-50 dark:bg-red-500/10'
                    : status === 'late' ? 'bg-amber-50 dark:bg-amber-500/10'
                    : status === 'excused' ? 'bg-blue-50 dark:bg-blue-500/10'
                    : '';
                  const icon = status === 'present' ? '✓' : status === 'absent' ? '✗' : status === 'late' ? '⏰' : status === 'excused' ? 'ℹ' : '○';
                  const iconColor = status === 'present' ? 'text-green-600'
                    : status === 'absent' ? 'text-red-600'
                    : status === 'late' ? 'text-amber-600'
                    : status === 'excused' ? 'text-blue-600'
                    : 'text-school-muted';
                  return (
                    <button
                      key={s.id}
                      onClick={() => cycleStatus(s.id)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-school-paper/50 dark:hover:bg-white/5 ${bgColor}`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        status !== 'unmarked' ? 'bg-white/80 dark:bg-white/10 shadow-sm ' + iconColor : 'bg-school-border/20 dark:bg-[#2a2a3e] text-school-muted'
                      }`}>
                        {icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm text-school-primary dark:text-[#e0e0e8] truncate">{s.name}</div>
                        {s.roll && <div className="text-[10px] text-school-muted">Roll {s.roll}</div>}
                      </div>
                      <div className="text-[10px] font-bold uppercase text-school-muted min-w-[48px] text-right">
                        {status === 'unmarked' ? 'Tap' : STATUS_NAMES[status]}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {students.length > 0 && (
              <button
                onClick={handleSave}
                disabled={saving || markedCount === 0}
                className="w-full px-4 py-3 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
              >
                {saving ? (
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                )}
                {saving ? 'Saving...' : `Save (${markedCount})`}
              </button>
            )}
          </>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="date"
                value={rangeFrom}
                onChange={(e) => setRangeFrom(e.target.value)}
                className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
              />
              <input
                type="date"
                value={rangeTo}
                onChange={(e) => setRangeTo(e.target.value)}
                className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select value={rangeTerm} onChange={(e) => setRangeTerm(e.target.value)} className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]">
                {Object.entries(TERM_NAMES).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
              <button
                onClick={loadRangeReport}
                disabled={!rangeFrom || !rangeTo || rangeLoading}
                className="w-full px-3 py-2 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
              >
                {rangeLoading ? (
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                )}
                {rangeLoading ? 'Loading...' : 'Load'}
              </button>
            </div>

            {rangeError && (
              <div className="text-center py-3 text-red-500 text-sm">{rangeError}</div>
            )}

            {rangeReport && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-school-muted">
                    {rangeReport.students.length} students · {rangeReport.dates.length} days
                  </span>
                </div>
                <div className="overflow-x-auto rounded-2xl border border-school-border dark:border-[#2a2a3e]">
                  <table className="w-full text-xs whitespace-nowrap">
                    <thead>
                      <tr className="bg-school-paper dark:bg-[#2a2a3e]">
                        <th className="sticky left-0 z-10 bg-school-paper dark:bg-[#2a2a3e] px-2 py-2 text-left font-bold text-school-muted uppercase tracking-wider min-w-[140px]">Student</th>
                        <th className="sticky left-[140px] z-10 bg-school-paper dark:bg-[#2a2a3e] px-2 py-2 text-center font-bold text-school-muted uppercase tracking-wider min-w-[36px]">R</th>
                        {rangeReport.dates.map((d) => (
                          <th key={d} className="px-1.5 py-2 text-center font-semibold text-school-muted min-w-[30px] text-[10px]">
                            {new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                          </th>
                        ))}
                        <th className="px-1.5 py-2 text-center font-bold text-green-700 dark:text-green-400 min-w-[24px]">✓</th>
                        <th className="px-1.5 py-2 text-center font-bold text-red-700 dark:text-red-400 min-w-[24px]">✗</th>
                        <th className="px-1.5 py-2 text-center font-bold text-amber-700 dark:text-amber-400 min-w-[24px]">⏰</th>
                        <th className="px-1.5 py-2 text-center font-bold text-blue-700 dark:text-blue-400 min-w-[24px]">ℹ</th>
                        <th className="px-1.5 py-2 text-center font-bold text-school-muted min-w-[36px] text-[10px]">%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rangeReport.students.map((s) => {
                        const sum = rangeReport.summary[s.id];
                        return (
                          <tr key={s.id} className="border-t border-school-border/50 dark:border-[#2a2a3e] hover:bg-school-paper/50 dark:hover:bg-white/5">
                            <td className="sticky left-0 z-10 bg-white dark:bg-[#1a1a2e] px-2 py-1.5 font-semibold text-school-primary dark:text-[#e0e0e8] truncate max-w-[140px] text-[11px]">{s.name}</td>
                            <td className="sticky left-[140px] z-10 bg-white dark:bg-[#1a1a2e] px-2 py-1.5 text-center text-school-muted text-[10px]">{s.roll || '—'}</td>
                            {rangeReport.dates.map((d) => {
                              const status = rangeReport.grid[s.id]?.[d];
                              const cellBg = !status ? 'bg-school-border/10'
                                : status === 'present' ? 'bg-green-100 dark:bg-green-500/20'
                                : status === 'absent' ? 'bg-red-100 dark:bg-red-500/20'
                                : status === 'late' ? 'bg-amber-100 dark:bg-amber-500/20'
                                : 'bg-blue-100 dark:bg-blue-500/20';
                              return (
                                <td key={d} className={`px-1.5 py-1.5 text-center text-[11px] ${cellBg}`}>
                                  {!status ? '—' : status === 'present' ? '✓' : status === 'absent' ? '✗' : status === 'late' ? '⏰' : 'ℹ'}
                                </td>
                              );
                            })}
                            <td className="px-1.5 py-1.5 text-center font-bold text-green-700 dark:text-green-400 text-[11px]">{sum.present}</td>
                            <td className="px-1.5 py-1.5 text-center font-bold text-red-700 dark:text-red-400 text-[11px]">{sum.absent}</td>
                            <td className="px-1.5 py-1.5 text-center font-bold text-amber-700 dark:text-amber-400 text-[11px]">{sum.late}</td>
                            <td className="px-1.5 py-1.5 text-center font-bold text-blue-700 dark:text-blue-400 text-[11px]">{sum.excused}</td>
                            <td className="px-1.5 py-1.5 text-center font-bold text-school-primary dark:text-[#e0e0e8] text-[11px]">{sum.pct}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
      <Toast />
    </div>
  );
}
