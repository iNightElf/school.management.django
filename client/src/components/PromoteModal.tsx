import { useState, useEffect } from 'react';
import { api } from '../store';
import { toast } from './Toast';
import { Loader2, Check, AlertTriangle, GraduationCap, ArrowRight, X } from 'lucide-react';

interface Props {
  open: boolean;
  targetYearName: string;
  targetAcademicYearId: string;
  onClose: () => void;
  onDone: () => void;
}

export default function PromoteModal({ open, targetYearName, targetAcademicYearId, onClose, onDone }: Props) {
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) { setPreview(null); setConfirming(false); setResult(null); setError(null); return; }
    setLoading(true);
    setError(null);
    api.post('/classes/promote-all/?dryRun=true', { targetYearName, targetAcademicYearId })
      .then(r => { setPreview(r.data); setLoading(false); })
      .catch((e) => {
        const msg = e?.response?.data?.error || e?.response?.data?.detail || e?.message || 'Failed to load preview';
        setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        setLoading(false);
      });
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleConfirm = async () => {
    setConfirming(true);
    setError(null);
    try {
      const res = await api.post('/classes/promote-all/', { targetYearName, targetAcademicYearId });
      const d = res.data;
      if (d.error) throw new Error(d.error);
      setResult(d);
      toast('Promotion complete', 'success');
      onDone();
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.response?.data?.detail || e?.message || 'Promotion failed';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      toast(msg, 'error');
    }
    setConfirming(false);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 pb-0">
          <h3 className="font-serif text-lg text-school-primary flex items-center gap-2">
            <GraduationCap size={20} /> Promote Students
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-school-paper rounded-lg transition-colors"><X size={18} /></button>
        </div>
        <div className="p-6 pt-3">
          <p className="text-xs text-school-muted mb-4">
            Target session: <span className="font-bold text-school-primary">{targetYearName}</span>
          </p>

          {loading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-12 gap-2 text-school-muted">
                <Loader2 size={20} className="animate-spin" /> Loading preview...
              </div>
              <button onClick={onClose} className="w-full py-2.5 border border-school-border rounded-xl text-sm hover:bg-school-paper">
                Cancel
              </button>
            </div>
          ) : error ? (
            <div className="space-y-4">
              <div className="flex items-start gap-2 text-rose-600 bg-rose-50 rounded-xl p-4 text-sm">
                <AlertTriangle size={18} className="mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-bold">Error</p>
                  <p className="mt-1 text-rose-700">{error}</p>
                </div>
              </div>
              <button onClick={onClose} className="w-full py-2.5 border border-school-border rounded-xl text-sm hover:bg-school-paper">
                Close
              </button>
            </div>
          ) : result ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-emerald-600 bg-emerald-50 rounded-xl p-3 text-sm font-bold">
                <Check size={18} /> Promotion completed successfully
              </div>
              {result.promoted.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase text-school-muted mb-2">Promoted</h4>
                  <div className="space-y-1">
                    {result.promoted.map((p: any, i: number) => (
                      <div key={i} className="flex items-center justify-between text-sm bg-blue-50 rounded-lg px-3 py-2">
                        <span>{p.from} <ArrowRight size={12} className="inline mx-1 text-school-muted" /> {p.to}</span>
                        <span className="font-bold">{p.count} student{p.count !== 1 ? 's' : ''}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {result.graduated.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase text-school-muted mb-2">Graduated</h4>
                  <div className="space-y-1">
                    {result.graduated.map((g: any, i: number) => (
                      <div key={i} className="flex items-center justify-between text-sm bg-amber-50 rounded-lg px-3 py-2">
                        <span>{g.from}</span>
                        <span className="font-bold">{g.count} student{g.count !== 1 ? 's' : ''}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <button onClick={onClose} className="w-full py-2.5 bg-school-primary text-white rounded-xl text-sm font-bold hover:opacity-90">
                Close
              </button>
            </div>
          ) : preview ? (
            <div className="space-y-4">
              {preview.promoted.length === 0 && preview.graduated.length === 0 ? (
                <div className="text-center py-8 text-school-muted text-sm">
                  <Check size={32} className="mx-auto mb-2 text-emerald-500" />
                  All students are already assigned to session {targetYearName}. Nothing to promote.
                </div>
              ) : (
                <>
                  {preview.promoted.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase text-school-muted mb-2">Will be Promoted</h4>
                      <div className="space-y-1">
                        {preview.promoted.map((p: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-sm bg-blue-50 rounded-lg px-3 py-2">
                            <span>
                              {p.from} <ArrowRight size={12} className="inline mx-1 text-school-muted" /> {p.to}
                              {p.newClass && <span className="ml-1 text-[10px] text-purple-600 font-bold">(new)</span>}
                            </span>
                            <span className="font-bold">{p.count} student{p.count !== 1 ? 's' : ''}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {preview.graduated.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase text-school-muted mb-2">Will be Graduated</h4>
                      <div className="space-y-1">
                        {preview.graduated.map((g: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-sm bg-amber-50 rounded-lg px-3 py-2">
                            <span>{g.from}</span>
                            <span className="font-bold">{g.count} student{g.count !== 1 ? 's' : ''}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2 text-sm">
                    <AlertTriangle size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
                    <span className="text-amber-800">This action cannot be undone. Student IDs will remain unchanged.</span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={onClose} className="flex-1 py-2.5 border border-school-border rounded-xl text-sm hover:bg-school-paper">
                      Cancel
                    </button>
                    <button onClick={handleConfirm} disabled={confirming} className="flex-1 py-2.5 bg-school-primary text-white rounded-xl text-sm font-bold hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-1">
                      {confirming ? <><Loader2 size={14} className="animate-spin" /> Promoting...</> : 'Confirm & Promote'}
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
