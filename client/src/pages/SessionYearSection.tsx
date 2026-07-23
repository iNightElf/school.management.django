import { useState, useEffect } from 'react';
import { useSchoolStore, api } from '../store';
import { Calendar, CalendarPlus, Plus, GraduationCap, Check } from 'lucide-react';
import { toast } from '../components/Toast';
import PromoteModal from '../components/PromoteModal';

function digitsOnly(v: string) { return v.replace(/\D/g, ''); }

export default function SessionYearSection() {
  const { academicYears: years, fetchAcademicYears, fetchClasses } = useSchoolStore();
  const [loading, setLoading] = useState(true);

  const [showYearForm, setShowYearForm] = useState(false);
  const [newDigits, setNewDigits] = useState('');
  const [creating, setCreating] = useState(false);

  const [showPromote, setShowPromote] = useState(false);
  const [promoteTarget, setPromoteTarget] = useState<{ name: string; id: string } | null>(null);

  const activeYear = years.find((y: any) => y.isActive);
  const fullName = (digits: string) => digits ? `FY${digits}` : '';

  useEffect(() => {
    Promise.all([fetchAcademicYears(true), fetchClasses()]).then(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCreateYear = async () => {
    const name = fullName(newDigits);
    if (!name) { toast('Enter a year (e.g. 2026)', 'error'); return; }
    if (years.some((y: any) => y.name === name)) { toast('Year already exists', 'error'); return; }
    setCreating(true);
    try {
      const startDate = `${newDigits}-01-01`;
      const endDate = `${newDigits}-12-31`;
      const res = await api.post('/academic-years/', { name, startDate, endDate, isActive: true });
      toast('Academic year created', 'success');
      setShowYearForm(false);
      setNewDigits('');
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
          <p className="text-[11px] text-school-muted">Year runs from January 1st to December 31st.</p>
          <div className="flex gap-2 items-center">
            <span className="text-sm font-bold text-school-muted flex-shrink-0">FY</span>
            <input
              type="text"
              inputMode="numeric"
              value={newDigits}
              onChange={e => setNewDigits(digitsOnly(e.target.value))}
              placeholder="2027"
              className="flex-1 max-w-[160px] border border-school-border rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-school-accent"
              onKeyDown={e => { if (e.key === 'Enter') handleCreateYear(); }}
            />
          </div>
          <button
            onClick={handleCreateYear}
            disabled={creating || !newDigits}
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
              .sort((a: any, b: any) => {
                const aNum = parseInt(a.name.replace(/^FY/, ''));
                const bNum = parseInt(b.name.replace(/^FY/, ''));
                return bNum - aNum;
              })
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
