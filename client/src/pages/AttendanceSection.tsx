import { useState, useEffect, useCallback } from 'react';
import { api, useSchoolStore } from '../store';
import Toast, { toast } from '../components/Toast';
import type {
  SchoolClass, AttendanceRecord, AttendanceMonthResponse,
  AttendanceSummary, ClassAttendanceReport,
} from '../lib/types';
import { TERM_NAMES } from '../lib/config';
import {
  CalendarCheck, Check, X, Clock, AlertCircle, Loader2,
  ChevronLeft, ChevronRight, Circle, Download,
} from 'lucide-react';

type StatusType = 'present' | 'absent' | 'late' | 'excused' | 'unmarked';

const STATUS_OPTIONS: { key: Exclude<StatusType, 'unmarked'>; label: string; color: string }[] = [
  { key: 'present', label: 'Present', color: 'bg-green-500' },
  { key: 'absent', label: 'Absent', color: 'bg-red-500' },
  { key: 'late', label: 'Late', color: 'bg-amber-500' },
  { key: 'excused', label: 'Excused', color: 'bg-blue-500' },
];

function todayStr() {
  const d = new Date();
  return d.toISOString().split('T')[0];
}

function monthName(m: number) {
  return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1] || 'Unknown';
}

export default function AttendanceSection() {
  const { classes, fetchClasses } = useSchoolStore();
  const [classId, setClassId] = useState('');
  const [date, setDate] = useState(todayStr());
  const [term, setTerm] = useState('1');
  const [session, setSession] = useState(String(new Date().getFullYear()));
  const [records, setRecords] = useState<Record<string, StatusType>>({});
  const [students, setStudents] = useState<{ id: string; name: string; roll: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<'daily' | 'monthly' | 'range'>('daily');

  useEffect(() => { fetchClasses(); }, []);

  useEffect(() => {
    if (classId) {
      fetchStudents();
    }
  }, [classId]);

  const fetchStudents = useCallback(async () => {
    if (!classId) return;
    setLoading(true);
    try {
      const res = await api.get('/students/', { params: { class_id: classId, limit: 200 } });
      const list = (res.data.results || res.data).map((s: any) => ({
        id: s.id,
        name: s.name,
        roll: s.roll || '',
      }));
      list.sort((a: any, b: any) => String(a.roll || '').localeCompare(String(b.roll || ''), undefined, { numeric: true }));
      setStudents(list);
    } catch { toast('Failed to load students', 'error'); }
    setLoading(false);
  }, [classId]);

  useEffect(() => {
    if (classId && date && tab === 'daily') {
      loadExistingAttendance();
    }
  }, [classId, date, tab]);

  const loadExistingAttendance = useCallback(async () => {
    if (!classId || !date) return;
    try {
      const res = await api.get('/attendance/', { params: { class_id: classId, date } });
      const data: AttendanceRecord[] = res.data.results || res.data;
      if (data.length > 0) {
        const map: Record<string, StatusType> = {};
        for (const r of data) {
          map[r.student] = r.status as StatusType;
        }
        setRecords(map);
        if (data[0].term) setTerm(data[0].term);
        if (data[0].session) setSession(data[0].session);
      } else {
        setRecords({});
      }
    } catch { setRecords({}); }
  }, [classId, date]);

  const markAllPresent = () => {
    const all: Record<string, StatusType> = {};
    for (const s of students) all[s.id] = 'present';
    setRecords(all);
  };

  const setStudentStatus = (studentId: string, status: StatusType) => {
    setRecords((prev) => ({ ...prev, [studentId]: status }));
  };

  const cycleStatus = (studentId: string) => {
    const current = records[studentId] || 'unmarked';
    const order: StatusType[] = ['unmarked', 'present', 'absent', 'late', 'excused'];
    const idx = order.indexOf(current);
    const next = order[(idx + 1) % order.length];
    setStudentStatus(studentId, next);
  };

  const handleSave = async () => {
    if (!classId || !date) {
      toast('Select a class and date', 'error');
      return;
    }
    
    // Filter out unmarked records before saving
    const markedRecords: Record<string, string> = {};
    Object.entries(records).forEach(([sid, status]) => {
      if (status !== 'unmarked') markedRecords[sid] = status;
    });

    if (Object.keys(markedRecords).length === 0) {
      toast('Mark at least one student', 'error');
      return;
    }
    setSaving(true);
    try {
      await api.post('/attendance/batch/', {
        school_class: classId,
        date,
        term,
        session,
        records: markedRecords,
      });
      toast('Attendance saved', 'success');
    } catch (e: any) {
      const msg = e.response?.data?.error || 'Failed to save attendance';
      toast(msg, 'error');
    }
    setSaving(false);
  };

  const monthYearNow = { year: new Date().getFullYear(), month: new Date().getMonth() + 1 };
  const [monthYear, setMonthYear] = useState(monthYearNow);
  const [monthData, setMonthData] = useState<AttendanceMonthResponse | null>(null);
  const [studentSearch, setStudentSearch] = useState('');
  const [monthStudent, setMonthStudent] = useState<{ id: string; name: string; roll: string } | null>(null);
  const [monthSummary, setMonthSummary] = useState<AttendanceSummary | null>(null);

  // Range Report state
  const [rangeFrom, setRangeFrom] = useState(() => {
    const d = new Date(); d.setDate(1); return d.toISOString().split('T')[0];
  });
  const [rangeTo, setRangeTo] = useState(() => {
    const d = new Date(); return d.toISOString().split('T')[0];
  });
  const [rangeTerm, setRangeTerm] = useState('1');
  const [rangeReport, setRangeReport] = useState<ClassAttendanceReport | null>(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState('');

  const loadRangeReport = useCallback(async () => {
    if (!classId || !rangeFrom || !rangeTo) return;
    setRangeLoading(true);
    setRangeError('');
    try {
      const res = await api.get('/attendance/class-report/', {
        params: { class_id: classId, from: rangeFrom, to: rangeTo, term: rangeTerm, session },
      });
      setRangeReport(res.data);
    } catch (e: any) {
      const msg = e.response?.data?.error || 'Failed to load report';
      setRangeError(msg);
      setRangeReport(null);
    }
    setRangeLoading(false);
  }, [classId, rangeFrom, rangeTo, rangeTerm, session]);

  const exportRangeCSV = () => {
    if (!rangeReport) return;
    const rows: string[] = [];
    const header = ['Student', 'Roll', ...rangeReport.dates, 'Present', 'Absent', 'Late', 'Excused', 'Percentage'];
    rows.push(header.map(c => `"${c}"`).join(','));

    for (const s of rangeReport.students) {
      const sum = rangeReport.summary[s.id];
      const dateCells = rangeReport.dates.map(d => {
        const st = rangeReport.grid[s.id]?.[d] || '';
        return `"${st}"`;
      });
      const row = [
        `"${s.name}"`, `"${s.roll || ''}""`,
        ...dateCells,
        sum.present, sum.absent, sum.late, sum.excused, `${sum.pct}%`,
      ];
      rows.push(row.join(','));
    }

    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${rangeReport.class.name}_${rangeFrom}_${rangeTo}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const fetchMonthData = useCallback(async () => {
    if (!classId) return;
    const sid = monthStudent?.id;
    if (!sid) return;
    setLoading(true);
    try {
      const [monthRes, summaryRes] = await Promise.all([
        api.get(`/attendance/student/${sid}/`, {
          params: { year: monthYear.year, month: monthYear.month },
        }),
        api.get('/attendance/summary/', {
          params: { student: sid, term, session, year: monthYear.year, month: monthYear.month },
        }),
      ]);
      setMonthData(monthRes.data);
      setMonthSummary(summaryRes.data);
    } catch { toast('Failed to load monthly data', 'error'); }
    setLoading(false);
  }, [classId, monthStudent?.id, monthYear, term, session]);

  useEffect(() => {
    if (tab === 'monthly' && classId && monthStudent) {
      fetchMonthData();
    }
  }, [tab, classId, monthStudent, monthYear, term, session]);

  const filteredStudents = students.filter(
    (s) => s.name.toLowerCase().includes(studentSearch.toLowerCase()),
  );

  const markedCount = Object.values(records).filter(s => s !== 'unmarked').length;

  return (
    <div className="space-y-4 animate-fade-in max-w-2xl mx-auto">
      <Toast />

      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-purple-100 dark:bg-purple-500/20 rounded-2xl flex items-center justify-center">
          <CalendarCheck size={22} className="text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 className="font-bold text-lg text-school-primary dark:text-[#e0e0e8]">Attendance</h2>
          <p className="text-xs text-school-muted">Track daily attendance</p>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex bg-school-border/30 dark:bg-[#2a2a3e]/50 rounded-xl p-1">
        <button
          onClick={() => setTab('daily')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-colors ${
            tab === 'daily' ? 'bg-white dark:bg-school-primary shadow-sm text-school-primary dark:text-white' : 'text-school-muted'
          }`}
        >
          Daily Marking
        </button>
        <button
          onClick={() => setTab('monthly')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-colors ${
            tab === 'monthly' ? 'bg-white dark:bg-school-primary shadow-sm text-school-primary dark:text-white' : 'text-school-muted'
          }`}
        >
          Monthly View
        </button>
        <button
          onClick={() => setTab('range')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-colors ${
            tab === 'range' ? 'bg-white dark:bg-school-primary shadow-sm text-school-primary dark:text-white' : 'text-school-muted'
          }`}
        >
          Range Report
        </button>
      </div>

      {tab === 'daily' ? (
        <>
          {/* Controls */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8] col-span-2 sm:col-span-1"
            >
              <option value="">Select Class</option>
              {classes.map((c: SchoolClass) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
            />
            <select value={term} onChange={(e) => setTerm(e.target.value)} className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]">
              {Object.entries(TERM_NAMES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <input
              type="number"
              value={session}
              onChange={(e) => setSession(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
              placeholder="Session"
            />
          </div>

          {/* Action Bar */}
          {students.length > 0 && (
            <div className="flex items-center justify-between gap-2">
              <button onClick={markAllPresent} className="px-3 py-1.5 border border-school-border rounded-xl text-xs font-semibold text-school-primary dark:text-[#e0e0e8] hover:bg-school-paper dark:hover:bg-white/5 transition-colors flex items-center gap-1.5">
                <Check size={14} /> Mark All Present
              </button>
              <span className="text-xs text-school-muted">
                {markedCount}/{students.length} marked
              </span>
            </div>
          )}

          {/* Student List */}
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 size={28} className="animate-spin text-school-muted" />
            </div>
          ) : students.length === 0 ? (
            <div className="text-center py-12 text-school-muted text-sm">
              {classId ? 'No students in this class' : 'Select a class to begin'}
            </div>
          ) : (
            <div className="bg-white dark:bg-[#1a1a2e] rounded-2xl border border-school-border dark:border-[#2a2a3e] divide-y divide-school-border/50 dark:divide-[#2a2a3e] overflow-hidden">
              {students.map((s) => {
                const status = records[s.id] || 'unmarked';
                const statusColor = status === 'present' ? 'bg-green-100 dark:bg-green-500/20 border-green-300 dark:border-green-500/30'
                  : status === 'absent' ? 'bg-red-100 dark:bg-red-500/20 border-red-300 dark:border-red-500/30'
                  : status === 'late' ? 'bg-amber-100 dark:bg-amber-500/20 border-amber-300 dark:border-amber-500/30'
                  : status === 'excused' ? 'bg-blue-100 dark:bg-blue-500/20 border-blue-300 dark:border-blue-500/30'
                  : 'bg-transparent border-transparent';
                const iconColor = status === 'present' ? 'text-green-600'
                  : status === 'absent' ? 'text-red-600'
                  : status === 'late' ? 'text-amber-600'
                  : status === 'excused' ? 'text-blue-600'
                  : 'text-school-muted';
                const StatusIcon = status === 'present' ? Check
                  : status === 'absent' ? X
                  : status === 'late' ? Clock
                  : status === 'excused' ? AlertCircle
                  : Circle;

                return (
                  <button
                    key={s.id}
                    onClick={() => cycleStatus(s.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-school-paper/50 dark:hover:bg-white/5 ${status !== 'unmarked' ? statusColor : ''}`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${status !== 'unmarked' ? 'bg-white/60 dark:bg-white/10' : 'bg-school-border/30 dark:bg-[#2a2a3e]'}`}>
                      <StatusIcon size={16} className={iconColor} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm text-school-primary dark:text-[#e0e0e8] truncate">{s.name}</div>
                      {s.roll && <div className="text-[10px] text-school-muted uppercase">Roll {s.roll}</div>}
                    </div>
                    <div className="flex gap-1">
                      {STATUS_OPTIONS.map((opt) => (
                        <div
                          key={opt.key}
                          className={`w-2 h-2 rounded-full ${
                            records[s.id] === opt.key ? opt.color : 'bg-school-border/40 dark:bg-[#3a3a4e]'
                          }`}
                        />
                      ))}
                    </div>
                    <div className="text-[10px] font-bold uppercase text-school-muted min-w-[48px] text-right">
                      {status === 'unmarked' ? 'Tap' : STATUS_OPTIONS.find(o => o.key === status)?.label}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Save Button */}
          {students.length > 0 && (
            <button
              onClick={handleSave}
              disabled={saving || markedCount === 0}
              className="w-full px-4 py-3 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {saving ? <Loader2 size={18} className="animate-spin" /> : <CalendarCheck size={18} />}
              {saving ? 'Saving...' : `Save Attendance (${markedCount})`}
            </button>
          )}
        </>
      ) : tab === 'monthly' ? (
        <>
          {/* Monthly View */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8] col-span-2 sm:col-span-1"
            >
              <option value="">Select Class</option>
              {classes.map((c: SchoolClass) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <select value={term} onChange={(e) => setTerm(e.target.value)} className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]">
              {Object.entries(TERM_NAMES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <input
              type="number"
              value={session}
              onChange={(e) => setSession(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
            />
          </div>

          {/* Month Picker + Student Search */}
          <div className="flex items-center gap-2">
            <button onClick={() => setMonthYear((p) => {
              const m = p.month - 1;
              return m < 1 ? { year: p.year - 1, month: 12 } : { year: p.year, month: m };
            })} className="p-2 hover:bg-school-paper dark:hover:bg-white/5 rounded-xl transition-colors">
              <ChevronLeft size={18} className="text-school-muted" />
            </button>
            <span className="flex-1 text-center font-bold text-sm text-school-primary dark:text-[#e0e0e8]">
              {monthName(monthYear.month)} {monthYear.year}
            </span>
            <button onClick={() => setMonthYear((p) => {
              const m = p.month + 1;
              return m > 12 ? { year: p.year + 1, month: 1 } : { year: p.year, month: m };
            })} className="p-2 hover:bg-school-paper dark:hover:bg-white/5 rounded-xl transition-colors">
              <ChevronRight size={18} className="text-school-muted" />
            </button>
          </div>

          <input
            type="text"
            value={studentSearch}
            onChange={(e) => setStudentSearch(e.target.value)}
            placeholder="Search student name..."
            className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]"
          />

          {/* Student list to pick for monthly view */}
          {studentSearch && (
            <div className="bg-white dark:bg-[#1a1a2e] rounded-2xl border border-school-border dark:border-[#2a2a3e] max-h-48 overflow-y-auto divide-y divide-school-border/50">
              {filteredStudents.map((s) => (
                <button
                  key={s.id}
                  onClick={() => { setMonthStudent(s); setStudentSearch(s.name); }}
                  className={`w-full text-left px-4 py-2.5 text-sm hover:bg-school-paper/50 dark:hover:bg-white/5 transition-colors ${
                    monthStudent?.id === s.id ? 'bg-purple-50 dark:bg-purple-500/10 font-semibold' : ''
                  }`}
                >
                  {s.name} {s.roll ? `(Roll ${s.roll})` : ''}
                </button>
              ))}
            </div>
          )}

          {/* Calendar Grid */}
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 size={28} className="animate-spin text-school-muted" />
            </div>
          ) : monthData ? (
            <div className="space-y-3">
              {/* Summary Bar */}
              {monthSummary && (
                <div className="grid grid-cols-5 gap-1.5 text-center">
                  {[
                    { label: 'Present', value: monthSummary.present, color: 'bg-green-500' },
                    { label: 'Absent', value: monthSummary.absent, color: 'bg-red-500' },
                    { label: 'Late', value: monthSummary.late, color: 'bg-amber-500' },
                    { label: 'Excused', value: monthSummary.excused, color: 'bg-blue-500' },
                    { label: 'Unmarked', value: monthSummary.unmarked, color: 'bg-gray-400' },
                  ].map((s) => (
                    <div key={s.label} className="text-center">
                      <div className="text-lg font-bold text-school-primary dark:text-[#e0e0e8]">{s.value}</div>
                      <div className="text-[9px] uppercase tracking-wider text-school-muted font-semibold">{s.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Weekday Headers */}
              <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-bold uppercase text-school-muted tracking-wider">
                {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d) => (
                  <div key={d} className="py-1">{d}</div>
                ))}
              </div>

              {/* Day Cells */}
              <div className="grid grid-cols-7 gap-1">
                {monthData.days.map((day, i) => {
                  const d = new Date(day.date + 'T00:00:00');
                  const firstDow = new Date(monthData.year, monthData.month - 1, 1).getDay();
                  const bgColor = day.type === 'weekend' ? 'bg-school-border/20 dark:bg-[#2a2a3e]/30'
                    : day.type === 'holiday' || day.type === 'de_facto_holiday' ? 'bg-amber-50 dark:bg-amber-500/10'
                    : day.status === 'present' ? 'bg-green-50 dark:bg-green-500/15'
                    : day.status === 'absent' ? 'bg-red-50 dark:bg-red-500/15'
                    : day.status === 'late' ? 'bg-amber-50 dark:bg-amber-500/15'
                    : day.status === 'excused' ? 'bg-blue-50 dark:bg-blue-500/15'
                    : 'bg-white dark:bg-[#1a1a2e]';
                  const dotColor = day.status === 'present' ? 'bg-green-500'
                    : day.status === 'absent' ? 'bg-red-500'
                    : day.status === 'late' ? 'bg-amber-500'
                    : day.status === 'excused' ? 'bg-blue-500'
                    : '';

                  return (
                    <div
                      key={day.date}
                      className={`aspect-square rounded-lg flex flex-col items-center justify-center text-xs border border-school-border/30 dark:border-[#2a2a3e] ${bgColor}`}
                      style={i === 0 ? { gridColumnStart: firstDow + 1 } : undefined}
                      title={day.type === 'holiday' ? day.holiday_name || 'Holiday' : day.type === 'de_facto_holiday' ? 'School closed' : day.type === 'weekend' ? 'Weekend' : day.status ? `Status: ${day.status}` : 'No record'}
                    >
                      <span className={`font-semibold text-[11px] ${
                        day.type === 'weekend' ? 'text-school-muted/50'
                        : day.type === 'holiday' || day.type === 'de_facto_holiday' ? 'text-amber-600 dark:text-amber-400'
                        : day.status ? 'text-school-primary dark:text-[#e0e0e8]'
                        : 'text-school-muted'
                      }`}>
                        {d.getDate()}
                      </span>
                      {dotColor && <div className={`w-1.5 h-1.5 rounded-full mt-0.5 ${dotColor}`} />}
                      {day.type === 'holiday' && <div className="text-[7px] text-amber-600 dark:text-amber-400 leading-none mt-0.5 truncate max-w-full px-0.5">H</div>}
                      {day.type === 'de_facto_holiday' && <div className="text-[7px] text-amber-600 dark:text-amber-400 leading-none mt-0.5">C</div>}
                    </div>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-3 text-[10px] text-school-muted pt-2 border-t border-school-border/30 dark:border-[#2a2a3e]">
                {[
                  { color: 'bg-green-500', label: 'Present' },
                  { color: 'bg-red-500', label: 'Absent' },
                  { color: 'bg-amber-500', label: 'Late' },
                  { color: 'bg-blue-500', label: 'Excused' },
                  { color: 'bg-amber-300', label: 'Holiday' },
                  { color: 'bg-school-border/40', label: 'No Record' },
                ].map((l) => (
                  <div key={l.label} className="flex items-center gap-1.5">
                    <div className={`w-2.5 h-2.5 rounded-full ${l.color}`} />
                    <span>{l.label}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-school-muted text-sm">
              {classId ? 'Search and select a student to view monthly attendance' : 'Select a class to begin'}
            </div>
          )}
        </>
      ) : (
        <>
          {/* Range Report */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8] col-span-2 sm:col-span-1"
            >
              <option value="">Select Class</option>
              {classes.map((c: SchoolClass) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
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
            <select value={rangeTerm} onChange={(e) => setRangeTerm(e.target.value)} className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-white dark:bg-[#1a1a2e] text-school-primary dark:text-[#e0e0e8]">
              {Object.entries(TERM_NAMES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <button
              onClick={loadRangeReport}
              disabled={!classId || !rangeFrom || !rangeTo || rangeLoading}
              className="w-full px-3 py-2 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {rangeLoading ? <Loader2 size={16} className="animate-spin" /> : <CalendarCheck size={16} />}
              {rangeLoading ? 'Loading...' : 'Load Report'}
            </button>
          </div>

          {rangeError && (
            <div className="text-center py-4 text-red-500 text-sm">{rangeError}</div>
          )}

          {rangeReport && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-xs text-school-muted">
                  {rangeReport.students.length} students · {rangeReport.dates.length} days
                </span>
                <button
                  onClick={exportRangeCSV}
                  className="px-3 py-1.5 border border-school-border rounded-xl text-xs font-semibold text-school-primary dark:text-[#e0e0e8] hover:bg-school-paper dark:hover:bg-white/5 transition-colors flex items-center gap-1.5"
                >
                  <Download size={14} /> CSV
                </button>
              </div>
              <div className="overflow-x-auto rounded-2xl border border-school-border dark:border-[#2a2a3e]">
                <table className="w-full text-xs whitespace-nowrap">
                  <thead>
                    <tr className="bg-school-paper dark:bg-[#2a2a3e]">
                      <th className="sticky left-0 z-10 bg-school-paper dark:bg-[#2a2a3e] px-3 py-2 text-left font-bold text-school-muted uppercase tracking-wider min-w-[160px]">Student</th>
                      <th className="sticky left-[160px] z-10 bg-school-paper dark:bg-[#2a2a3e] px-3 py-2 text-center font-bold text-school-muted uppercase tracking-wider min-w-[44px]">Roll</th>
                      {rangeReport.dates.map((d) => (
                        <th key={d} className="px-2 py-2 text-center font-semibold text-school-muted min-w-[36px]">
                          {new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                        </th>
                      ))}
                      <th className="px-2 py-2 text-center font-bold text-green-700 dark:text-green-400 min-w-[28px]">✓</th>
                      <th className="px-2 py-2 text-center font-bold text-red-700 dark:text-red-400 min-w-[28px]">✗</th>
                      <th className="px-2 py-2 text-center font-bold text-amber-700 dark:text-amber-400 min-w-[28px]">⏰</th>
                      <th className="px-2 py-2 text-center font-bold text-blue-700 dark:text-blue-400 min-w-[28px]">ℹ</th>
                      <th className="px-2 py-2 text-center font-bold text-school-muted min-w-[44px]">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rangeReport.students.map((s) => {
                      const sum = rangeReport.summary[s.id];
                      return (
                        <tr key={s.id} className="border-t border-school-border/50 dark:border-[#2a2a3e] hover:bg-school-paper/50 dark:hover:bg-white/5">
                          <td className="sticky left-0 z-10 bg-white dark:bg-[#1a1a2e] px-3 py-1.5 font-semibold text-school-primary dark:text-[#e0e0e8] truncate max-w-[160px]">{s.name}</td>
                          <td className="sticky left-[160px] z-10 bg-white dark:bg-[#1a1a2e] px-3 py-1.5 text-center text-school-muted">{s.roll || '—'}</td>
                          {rangeReport.dates.map((d) => {
                            const status = rangeReport.grid[s.id]?.[d];
                            const cellClass = !status ? 'bg-school-border/10'
                              : status === 'present' ? 'bg-green-100 dark:bg-green-500/20'
                              : status === 'absent' ? 'bg-red-100 dark:bg-red-500/20'
                              : status === 'late' ? 'bg-amber-100 dark:bg-amber-500/20'
                              : 'bg-blue-100 dark:bg-blue-500/20';
                            const tip = status ? `${s.name} - ${d}: ${status}` : `${s.name} - ${d}: —`;
                            return (
                              <td key={d} className={`px-2 py-1.5 text-center ${cellClass}`} title={tip}>
                                {!status ? '—' : status === 'present' ? '✓' : status === 'absent' ? '✗' : status === 'late' ? '⏰' : 'ℹ'}
                              </td>
                            );
                          })}
                          <td className="px-2 py-1.5 text-center font-bold text-green-700 dark:text-green-400">{sum.present}</td>
                          <td className="px-2 py-1.5 text-center font-bold text-red-700 dark:text-red-400">{sum.absent}</td>
                          <td className="px-2 py-1.5 text-center font-bold text-amber-700 dark:text-amber-400">{sum.late}</td>
                          <td className="px-2 py-1.5 text-center font-bold text-blue-700 dark:text-blue-400">{sum.excused}</td>
                          <td className="px-2 py-1.5 text-center font-bold text-school-primary dark:text-[#e0e0e8]">{sum.pct}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
