import { useState, useEffect, useCallback } from 'react';
import { api } from '../../store';
import LessonPlanModal from './LessonPlanModal';
import { ChevronLeft, ChevronRight, Check, Loader2 } from 'lucide-react';

interface Period {
  id: string;
  day: string;
  period_number: number;
  subject_name: string;
  teacher_name: string;
  lesson_plan: {
    id: string;
    topic: string;
    learning_objectives: string;
    activities: string;
    materials: string;
    assessment: string;
    remarks: string;
    completed: boolean;
  } | null;
}

interface WeekData {
  week_start: string;
  week_end: string;
  periods: Period[];
}

const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'];
const DAY_LABELS: Record<string, string> = {
  sunday: 'Sun', monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu',
};

function getWeekStart(d: Date) {
  const day = d.getDay();
  const diff = d.getDate() - day;
  const start = new Date(d);
  start.setDate(diff);
  return start.toISOString().split('T')[0];
}

export default function WeeklyRoutine() {
  const [weekData, setWeekData] = useState<WeekData | null>(null);
  const [loading, setLoading] = useState(true);
  const [weekStart, setWeekStart] = useState(() => getWeekStart(new Date()));
  const [selectedPeriod, setSelectedPeriod] = useState<Period | null>(null);
  const [showModal, setShowModal] = useState(false);

  const fetchWeek = useCallback(async (ws: string) => {
    setLoading(true);
    try {
      const res = await api.get('/teacher/routine/week/', { params: { week: ws } });
      setWeekData(res.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchWeek(weekStart); }, [weekStart, fetchWeek]);

  const navigateWeek = (dir: number) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + dir * 7);
    setWeekStart(d.toISOString().split('T')[0]);
  };

  const handleCellClick = (p: Period) => {
    setSelectedPeriod(p);
    setShowModal(true);
  };

  const handlePlanSaved = () => {
    setShowModal(false);
    setSelectedPeriod(null);
    fetchWeek(weekStart);
  };

  const periods = weekData?.periods || [];
  const maxPeriod = Math.max(...periods.map((p) => p.period_number), 0);

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center justify-between">
        <button onClick={() => navigateWeek(-1)} className="p-2 hover:bg-school-paper dark:hover:bg-white/5 rounded-xl transition-colors">
          <ChevronLeft size={20} className="text-school-muted" />
        </button>
        <div className="text-center">
          <div className="font-bold text-sm text-school-primary dark:text-[#e0e0e8]">
            {weekData ? `${weekData.week_start} — ${weekData.week_end}` : weekStart}
          </div>
          <div className="text-[10px] text-school-muted">Weekly Plan</div>
        </div>
        <button onClick={() => navigateWeek(1)} className="p-2 hover:bg-school-paper dark:hover:bg-white/5 rounded-xl transition-colors">
          <ChevronRight size={20} className="text-school-muted" />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 size={28} className="animate-spin text-school-muted" /></div>
      ) : periods.length === 0 ? (
        <div className="text-center py-12 text-school-muted text-sm">No routine set for this week</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr>
                <th className="px-2 py-2 text-school-muted font-bold text-[10px] uppercase sticky left-0 bg-school-paper z-10">#</th>
                {DAYS.map((d) => (
                  <th key={d} className="px-2 py-2 text-school-muted font-bold text-[10px] uppercase min-w-[100px]">{DAY_LABELS[d]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: maxPeriod }, (_, i) => i + 1).map((pn) => (
                <tr key={pn}>
                  <td className="px-2 py-1 text-school-muted font-bold text-[10px] sticky left-0 bg-school-paper z-10 border-t border-school-border/30">{pn}</td>
                  {DAYS.map((d) => {
                    const p = periods.find((pr) => pr.day === d && pr.period_number === pn);
                    return (
                      <td key={d} className="px-1 py-1 border-t border-school-border/30">
                        {p ? (
                          <button
                            onClick={() => handleCellClick(p)}
                            className={`w-full min-h-[60px] rounded-xl p-2 text-left transition-colors border ${
                              p.lesson_plan?.completed
                                ? 'bg-green-50 dark:bg-green-500/10 border-green-200 dark:border-green-500/20'
                                : p.lesson_plan
                                ? 'bg-white dark:bg-[#1a1a2e] border-school-border dark:border-[#2a2a3e] hover:border-school-accent/50'
                                : 'bg-white dark:bg-[#1a1a2e] border-dashed border-school-border/50 dark:border-[#2a2a3e]/50 hover:border-school-accent/30'
                            }`}
                          >
                            <div className="font-bold text-school-primary dark:text-[#e0e0e8] truncate leading-tight">
                              {p.subject_name}
                            </div>
                            {p.lesson_plan && (
                              <div className="text-[9px] text-school-muted mt-0.5 line-clamp-2 leading-tight">
                                {p.lesson_plan.topic}
                              </div>
                            )}
                            {p.lesson_plan?.completed && (
                              <div className="flex items-center gap-0.5 mt-0.5 text-[8px] text-green-600 font-bold">
                                <Check size={10} /> Done
                              </div>
                            )}
                          </button>
                        ) : (
                          <div className="min-h-[60px]" />
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && selectedPeriod && (
        <LessonPlanModal
          period={selectedPeriod}
          weekStart={weekStart}
          onSave={handlePlanSaved}
          onClose={() => { setShowModal(false); setSelectedPeriod(null); }}
        />
      )}
    </div>
  );
}
