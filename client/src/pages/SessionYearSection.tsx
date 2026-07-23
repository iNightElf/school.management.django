import { useState, useEffect } from 'react';
import { useSchoolStore, api } from '../store';
import { Calendar, CalendarPlus, Plus, GraduationCap, Check } from 'lucide-react';
import { toast } from '../components/Toast';
import PromoteModal from '../components/PromoteModal';

export default function SessionYearSection() {
  const { academicYears: years, fetchAcademicYears, fetchClasses } = useSchoolStore();
  const [loading, setLoading] = useState(true);

  const [showYearForm, setShowYearForm] = useState(false);
  const [yearForm, setYearForm] = useState({ name: '', startDate: '', endDate: '' });
  const [creating, setCreating] = useState(false);

  const [showPromote, setShowPromote] = useState(false);
  const [promoteTarget, setPromoteTarget] = useState<{ name: string; id: string } | null>(null);

  const activeYear = years.find((y: any) => y.isActive);

  useEffect(() => {
    Promise.all([fetchAcademicYears(true), fetchClasses()]).then(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-suggest year name when both dates are filled
  useEffect(() => {
    if (yearForm.startDate && yearForm.endDate) {
      const startYear = new Date(yearForm.startDate).getFullYear();
      const endYear = new Date(yearForm.endDate).getFullYear();
      if (endYear > startYear) {
        setYearForm(prev => ({ ...prev, name: `${startYear}-${endYear}` }));
      } else {
        setYearForm(prev => ({ ...prev, name: `${startYear}` }));
      }
    }
  }, [yearForm.startDate, yearForm.endDate]);

  const handleCreateYear = async () => {
    if (!yearForm.name || !yearForm.startDate || !yearForm.endDate) {
      toast('Name, start date, and end date required', 'error');
      return;
    }
    if (new Date(yearForm.startDate).getFullYear() !== new Date(yearForm.endDate).getFullYear()) {
      toast('Start and end date must be in the same year', 'error');
      return;
    }
    setCreating(true);
    try {
      const res = await api.post('/academic-years/', { ...yearForm, isActive: true });
      toast('Academic year created', 'success');
      setShowYearForm(false);
      setYearForm({ name: '', startDate: '', endDate: '' });
      setShowPromote(true);
      setPromoteTarget({ name: res.data.name, id: res.data.id });
      fetchAcademicYears(true);
    } catch (e: any) {
      const msg = e?.response?.data?.error || (e?.response?.data ? Object.values(e.response.data).flat().join(', ') : 'Failed to create academic year');
      toast(msg, 'error');
    }
    setCreating(false);
  };

  const handleSetActive = async (id: string) => {
    try {
      await api.patch(`/academic-years/${id}/`, { isActive: true });
      toast('Active year changed', 'success');
      fetchAcademicYears(true);
    } catch (err: any) {
      toast(err?.response?.data?.detail || 'Failed to update', 'error');
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-2">
          <Calendar size={20} className="text-school-accent" />
          <h2 className="text-sm font-bold text-school-primary">Session / Academic Year</h2>
        </div>
        <div className="space-y-2">
          {[0, 1, 2].map(i => <div key={i} className="h-12 bg-school-paper rounded-xl animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar size={20} className="text-school-accent" />
          <h2 className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">Session / Academic Year</h2>
          {activeYear && (
            <span className="text-[10px] bg-school-primary/10 text-school-primary px-2 py-0.5 rounded font-bold">
              {activeYear.name}
            </span>
          )}
        </div>
        <button
          onClick={() => setShowYearForm(!showYearForm)}
          className="flex items-center gap-1.5 px-3 py-2 bg-amber-500 text-white rounded-xl text-xs font-bold hover:opacity-90 transition-opacity"
        >
          <CalendarPlus size={14} /> {showYearForm ? 'Cancel' : 'New Year'}
        </button>
      </div>

      {/* Active Year Card */}
      {activeYear && (
        <div className="bg-gradient-to-r from-school-primary to-indigo-700 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase font-bold opacity-70">Current Session</p>
              <p className="text-lg font-bold">{activeYear.name}</p>
              <p className="text-xs opacity-70 mt-0.5">
                {activeYear.startDate ? new Date(activeYear.startDate).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                {' → '}
                {activeYear.endDate ? new Date(activeYear.endDate).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
              </p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Check size={24} />
            </div>
          </div>
        </div>
      )}

      {/* Create Year Form */}
      {showYearForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <h4 className="font-bold text-xs text-school-primary dark:text-[#e0e0e8]">Create New Academic Year</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] font-bold uppercase text-school-muted block mb-1">Year Name</label>
              <input
                value={yearForm.name}
                onChange={e => setYearForm({ ...yearForm, name: e.target.value })}
                placeholder="e.g. 2026-2027"
                className="w-full border border-school-border rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-school-accent"
              />
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase text-school-muted block mb-1">Start Date</label>
              <input
                type="date"
                value={yearForm.startDate}
                onChange={e => setYearForm({ ...yearForm, startDate: e.target.value })}
                className="w-full border border-school-border rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-school-accent"
              />
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase text-school-muted block mb-1">End Date</label>
              <input
                type="date"
                value={yearForm.endDate}
                onChange={e => setYearForm({ ...yearForm, endDate: e.target.value })}
                className="w-full border border-school-border rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-school-accent"
              />
            </div>
          </div>
          <button
            onClick={handleCreateYear}
            disabled={creating}
            className="flex items-center gap-1.5 px-4 py-2 bg-school-primary text-white rounded-xl text-sm font-bold hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            <Plus size={14} /> Create Academic Year
          </button>
        </div>
      )}

      {/* Promote Banner */}
      {showPromote && promoteTarget && (
        <div className="bg-gradient-to-r from-purple-600 to-indigo-700 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-bold text-sm flex items-center gap-1.5">
                <GraduationCap size={16} /> New Academic Year Created
              </h4>
              <p className="text-xs text-purple-200 mt-0.5">
                Session: <span className="font-bold text-white">{promoteTarget.name}</span>
              </p>
              <p className="text-xs text-purple-200 mt-1">
                Promote all students to the next class for the new session?
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPromote(true)}
                className="px-4 py-2 bg-white text-purple-700 rounded-lg text-xs font-bold hover:bg-purple-50 transition-colors"
              >
                Promote All →
              </button>
              <button
                onClick={() => { setShowPromote(false); setPromoteTarget(null); }}
                className="px-3 py-2 border border-purple-400 text-purple-200 rounded-lg text-xs hover:bg-white/10 transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
      <PromoteModal
        open={showPromote && !!promoteTarget}
        targetYearName={promoteTarget?.name || ''}
        targetAcademicYearId={promoteTarget?.id || ''}
        onClose={() => { setShowPromote(false); setPromoteTarget(null); }}
        onDone={() => { setShowPromote(false); setPromoteTarget(null); }}
      />

      {/* All Years */}
      <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
        <h4 className="font-bold text-xs text-school-primary dark:text-[#e0e0e8] mb-3">
          All Academic Years ({years.length})
        </h4>
        {years.length === 0 ? (
          <p className="text-sm text-school-muted text-center py-4">No academic years yet. Create one to get started.</p>
        ) : (
          <div className="space-y-1">
            {[...years]
              .sort((a: any, b: any) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime())
              .map((y: any) => (
                <div
                  key={y.id}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm ${
                    y.isActive
                      ? 'bg-school-primary/10 text-school-primary font-bold'
                      : 'hover:bg-school-paper/50'
                  }`}
                >
                  <div>
                    <span className="font-semibold">{y.name}</span>
                    <span className="text-[10px] text-school-muted ml-2">
                      {y.startDate ? new Date(y.startDate).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '—'}
                      {' — '}
                      {y.endDate ? new Date(y.endDate).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' }) : '—'}
                    </span>
                  </div>
                  <div>
                    {y.isActive ? (
                      <span className="text-[10px] bg-school-primary text-white px-2 py-0.5 rounded-full font-bold">Active</span>
                    ) : (
                      <button
                        onClick={() => handleSetActive(y.id)}
                        className="text-[10px] px-2 py-0.5 border border-school-border rounded-lg hover:border-school-accent transition-colors"
                      >
                        Set Active
                      </button>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
