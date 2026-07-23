import { useState, useEffect } from 'react';
import { api } from '../store';
import { toast, getErrorMessage } from '../components/Toast';
import { Loader2, Plus, X, Trash2, Calendar } from 'lucide-react';

interface RoutinePeriod {
  id: string;
  schoolClass: string;
  day: string;
  periodNumber: number;
  subject: string;
  subjectName: string;
  teacher: string;
  teacherName: string;
}

interface PeriodTime {
  period_number: number;
  start_time: string;
  end_time: string;
}

const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'];
const DAY_LABELS: Record<string, string> = {
  sunday: 'Sunday', monday: 'Monday', tuesday: 'Tuesday', wednesday: 'Wednesday', thursday: 'Thursday',
};

function getWeekStart() {
  const now = new Date();
  now.setDate(now.getDate() - now.getDay());
  return now.toISOString().split('T')[0];
}

export default function AdminRoutine() {
  const [classes, setClasses] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [routines, setRoutines] = useState<RoutinePeriod[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [loading, setLoading] = useState(false);
  const [editCell, setEditCell] = useState<{ day: string; period: number } | null>(null);
  const [editSubject, setEditSubject] = useState('');
  const [editTeacher, setEditTeacher] = useState('');
  const [editTopic, setEditTopic] = useState('');
  const [editId, setEditId] = useState('');
  const [saving, setSaving] = useState(false);
  const [periodCount, setPeriodCount] = useState(4);
  const [periodTimes, setPeriodTimes] = useState<Record<number, PeriodTime>>({});
  const [topics, setTopics] = useState<Record<string, string>>({});
  const [editingTime, setEditingTime] = useState<number | null>(null);
  const [editStartTime, setEditStartTime] = useState('');
  const [editEndTime, setEditEndTime] = useState('');

  const weekStart = getWeekStart();

  useEffect(() => {
    Promise.all([
      api.get('/classes/').then(r => setClasses(r.data?.results || r.data || [])),
      api.get('/teachers/', { params: { limit: '2000' } }).then(r => setTeachers(r.data?.results || r.data || [])),
      api.get('/academic/period-settings/').then(r => {
        const times: Record<number, PeriodTime> = {};
        (r.data || []).forEach((pt: PeriodTime) => { times[pt.period_number] = pt; });
        setPeriodTimes(times);
        const max = Math.max(...(r.data || []).map((pt: PeriodTime) => pt.period_number), 0);
        if (max > 0) setPeriodCount(prev => Math.max(prev, max));
      }).catch(() => {}),
    ]).catch(() => toast('Failed to load data', 'error'));
  }, []);

  useEffect(() => {
    if (!selectedClass) { setRoutines([]); setTopics({}); return; }
    setLoading(true);
    Promise.all([
      api.get('/classes/' + selectedClass + '/subjects/')
        .then(r => setSubjects(r.data?.results || r.data || []))
        .catch(() => setSubjects([])),
      api.get('/academic/routine-templates/', { params: { school_class: selectedClass } })
        .then(r => {
          const data = r.data?.results || r.data || [];
          setRoutines(data);
          const max = Math.max(...data.map((rt: any) => rt.period_number), 0);
          setPeriodCount(prev => Math.max(prev, max, 4));
        }).catch(() => setRoutines([])),
      api.get('/teacher/routine/week/', { params: { week: weekStart } })
        .then(r => {
          const periods = r.data?.periods || [];
          const classPeriods = periods.filter((p: any) => p.school_class === selectedClass);
          const map: Record<string, string> = {};
          classPeriods.forEach((p: any) => {
            if (p.lesson_plan?.topic) map[p.id] = p.lesson_plan.topic;
          });
          setTopics(map);
        }).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [selectedClass, weekStart]);

  const getCell = (day: string, period: number) =>
    routines.find(r => r.day === day && r.periodNumber === period);

  const getTopic = (day: string, period: number) => {
    const r = getCell(day, period);
    return r ? topics[r.id] || '' : '';
  };

  const openAdd = (day: string, period: number) => {
    const existing = getCell(day, period);
    setEditCell({ day, period });
    setEditSubject(existing?.subject || '');
    setEditTeacher(existing?.teacher || '');
    setEditTopic(getTopic(day, period));
    setEditId(existing?.id || '');
  };

  const closeEdit = () => {
    setEditCell(null);
    setEditSubject('');
    setEditTeacher('');
    setEditTopic('');
    setEditId('');
  };

  const handleSave = async () => {
    if (!editSubject || !editTeacher) return toast('Select subject and teacher', 'error');
    if (!editCell) return;
    setSaving(true);
    try {
      const payload = {
        school_class: selectedClass, day: editCell.day,
        period_number: editCell.period, subject: editSubject, teacher: editTeacher,
      };
      let routineId = editId;
      if (routineId) {
        await api.put('/academic/routine-templates/' + routineId + '/', payload);
      } else {
        const res = await api.post('/academic/routine-templates/', payload);
        routineId = res.data.id;
        setEditId(routineId);
      }
      if (editTopic && routineId) {
        await api.post('/teacher/routine/lesson_plan/', {
          routine_template: routineId, week_start: weekStart, topic: editTopic,
        });
      }
      toast('Period saved', 'success');
      const res = await api.get('/academic/routine-templates/', { params: { school_class: selectedClass } });
      setRoutines(res.data?.results || res.data || []);
      closeEdit();
    } catch (e: any) {
      toast(getErrorMessage(e), 'error');
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this period?')) return;
    try {
      await api.delete('/academic/routine-templates/' + id + '/');
      toast('Period removed', 'success');
      setRoutines(prev => prev.filter(r => r.id !== id));
      closeEdit();
    } catch { toast('Failed to delete', 'error'); }
  };

  const openTimeEdit = (pn: number) => {
    const t = periodTimes[pn];
    setEditingTime(pn);
    setEditStartTime(t?.start_time || '');
    setEditEndTime(t?.end_time || '');
  };

  const closeTimeEdit = () => setEditingTime(null);

  const saveTime = async (pn: number) => {
    const all = { ...periodTimes, [pn]: { period_number: pn, start_time: editStartTime, end_time: editEndTime } };
    const list = Object.values(all).sort((a, b) => a.period_number - b.period_number);
    try {
      await api.put('/academic/period-settings/', list);
      setPeriodTimes(all);
      setEditingTime(null);
      toast('Time saved', 'success');
    } catch { toast('Failed to save time', 'error'); }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center gap-3">
        <Calendar size={20} className="text-school-accent" />
        <h2 className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">Routine Management</h2>
      </div>

      <select value={selectedClass} onChange={e => { setSelectedClass(e.target.value); closeEdit(); }}
        className="w-full max-w-xs border border-school-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-school-accent">
        <option value="">Select a class</option>
        {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>

      {selectedClass && (
        loading ? (
          <div className="flex justify-center py-12"><Loader2 size={24} className="animate-spin text-school-muted" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr>
                  <th className="px-2 py-2 text-school-muted font-bold text-[10px] uppercase w-16 text-left">Day</th>
                  {Array.from({ length: periodCount }, (_, i) => i + 1).map(pn => (
                    <th key={pn} className="px-2 py-2 text-school-muted font-bold text-[10px] uppercase min-w-[130px]">
                      <div>Period {pn}</div>
                      <div className="mt-1 font-normal">
                        {editingTime === pn ? (
                          <span className="inline-flex items-center gap-1">
                            <input value={editStartTime} onChange={e => setEditStartTime(e.target.value)}
                              className="w-12 border border-school-border rounded px-1 py-0.5 text-[9px] outline-none text-center" placeholder="9:00" />
                            <span className="text-school-muted/50">-</span>
                            <input value={editEndTime} onChange={e => setEditEndTime(e.target.value)}
                              className="w-12 border border-school-border rounded px-1 py-0.5 text-[9px] outline-none text-center" placeholder="10:00" />
                            <button onClick={() => saveTime(pn)}
                              className="text-green-600 hover:text-green-700 font-bold text-[10px]">✓</button>
                            <button onClick={closeTimeEdit}
                              className="text-school-muted hover:text-school-primary text-[10px]">✕</button>
                          </span>
                        ) : (
                          <button onClick={() => openTimeEdit(pn)}
                            className="hover:text-school-accent transition-colors cursor-pointer">
                            {periodTimes[pn] ? `${periodTimes[pn].start_time} - ${periodTimes[pn].end_time}` : '+ set time'}
                          </button>
                        )}
                      </div>
                    </th>
                  ))}
                  <th className="px-2 py-2 w-8">
                    <button onClick={() => setPeriodCount(prev => prev + 1)}
                      className="w-7 h-7 flex items-center justify-center rounded-full border border-dashed border-school-border/40 hover:border-school-accent hover:bg-school-accent/5 transition-colors cursor-pointer"
                      title="Add period">
                      <Plus size={14} className="text-school-muted/40" />
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {DAYS.map(day => (
                  <tr key={day}>
                    <td className="px-2 py-1 text-school-muted font-bold text-[10px] border-t border-school-border/30">{DAY_LABELS[day]}</td>
                    {Array.from({ length: periodCount }, (_, i) => i + 1).map(pn => {
                      const p = getCell(day, pn);
                      const isEditing = editCell?.day === day && editCell?.period === pn;
                      return (
                        <td key={pn} className="px-1 py-1 border-t border-school-border/30">
                          {isEditing ? (
                            <div className="bg-white dark:bg-[#1a1a2e] rounded-xl p-2 border-2 border-school-accent space-y-1.5 min-h-[110px]">
                              <select value={editSubject} onChange={e => setEditSubject(e.target.value)}
                                className="w-full border border-school-border rounded px-1.5 py-1 text-[10px] outline-none">
                                <option value="">Subject</option>
                                {subjects.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                              </select>
                              <select value={editTeacher} onChange={e => setEditTeacher(e.target.value)}
                                className="w-full border border-school-border rounded px-1.5 py-1 text-[10px] outline-none">
                                <option value="">Teacher</option>
                                {teachers.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
                              </select>
                              <input value={editTopic} onChange={e => setEditTopic(e.target.value)}
                                className="w-full border border-school-border rounded px-1.5 py-1 text-[10px] outline-none"
                                placeholder="Lesson topic" />
                              <div className="flex gap-1">
                                <button onClick={handleSave} disabled={saving}
                                  className="flex-1 bg-school-accent text-white rounded text-[9px] font-bold py-1 disabled:opacity-50">Save</button>
                                {editId && (
                                  <button onClick={() => handleDelete(editId)}
                                    className="p-1 text-red-500 hover:bg-red-50 rounded"><Trash2 size={12} /></button>
                                )}
                                <button onClick={closeEdit} className="p-1 text-school-muted hover:bg-school-border/30 rounded"><X size={12} /></button>
                              </div>
                            </div>
                          ) : p ? (
                            <button onClick={() => openAdd(day, pn)}
                              className="w-full text-left bg-white dark:bg-[#1a1a2e] rounded-xl p-2 border border-school-border dark:border-[#2a2a3e] min-h-[50px] hover:border-school-accent transition-colors cursor-pointer">
                              <div className="font-bold text-school-primary dark:text-[#e0e0e8] text-[11px] leading-tight">{p.subjectName}</div>
                              <div className="text-[8px] text-school-muted mt-0.5">{p.teacherName}</div>
                              {getTopic(day, pn) && (
                                <div className="text-[8px] text-school-accent mt-0.5 truncate">{getTopic(day, pn)}</div>
                              )}
                            </button>
                          ) : (
                            <button onClick={() => openAdd(day, pn)}
                              className="w-full min-h-[50px] rounded-xl border border-dashed border-school-border/40 flex items-center justify-center hover:border-school-accent hover:bg-school-accent/5 transition-colors cursor-pointer">
                              <Plus size={14} className="text-school-muted/40" />
                            </button>
                          )}
                        </td>
                      );
                    })}
                    <td className="px-1 py-1 border-t border-school-border/30" />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}
