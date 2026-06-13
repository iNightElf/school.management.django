import { useEffect, useState } from 'react';
import { useSchoolStore } from '../../store';
import { Plus, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

const STATUS_ICONS = {
  pending: <Clock size={14} className="text-amber-500" />,
  completed: <CheckCircle size={14} className="text-green-500" />,
  overdue: <AlertTriangle size={14} className="text-red-500" />,
};

const InterventionsTab = () => {
  const { interventions, fetchInterventions, createIntervention, alerts, fetchAlerts } = useSchoolStore();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [form, setForm] = useState({ alert: '', actionTaken: '', followupDate: '', remarks: '', status: 'pending' });

  useEffect(() => { fetchInterventions(); fetchAlerts(); }, []);

  const filtered = filter === 'all' ? interventions : interventions.filter(i => i.status === filter);

  const handleSubmit = async () => {
    if (!form.alert || !form.actionTaken) return;
    await createIntervention(form);
    setForm({ alert: '', actionTaken: '', followupDate: '', remarks: '', status: 'pending' });
    setShowForm(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Interventions</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors">
          <Plus size={14} /> New Intervention
        </button>
      </div>

      <div className="flex gap-2">
        {['all', 'pending', 'completed', 'overdue'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-colors ${filter === s ? 'bg-school-primary text-white' : 'bg-white border border-school-border text-school-muted hover:border-school-accent'}`}>
            {s}
          </button>
        ))}
      </div>

      {showForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <select value={form.alert} onChange={e => setForm(f => ({ ...f, alert: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
            <option value="">Select Alert</option>
            {alerts.filter(a => a.status !== 'resolved').map(a => (
              <option key={a.id} value={a.id}>{a.title} - {a.studentName}</option>
            ))}
          </select>
          <input type="text" placeholder="Action Taken" value={form.actionTaken} onChange={e => setForm(f => ({ ...f, actionTaken: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          <div className="grid grid-cols-2 gap-2">
            <input type="date" value={form.followupDate} onChange={e => setForm(f => ({ ...f, followupDate: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
            <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <textarea placeholder="Remarks (optional)" value={form.remarks} onChange={e => setForm(f => ({ ...f, remarks: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" rows={2} />
          <div className="flex gap-2">
            <button onClick={handleSubmit} className="px-4 py-2 bg-school-primary text-white text-sm font-bold rounded-lg hover:bg-school-primary/90 transition-colors">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-100 text-school-muted text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {filtered.length === 0 && <div className="text-center py-8 text-school-muted text-sm">No interventions found</div>}
        {filtered.map(i => (
          <div key={i.id} className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5">{STATUS_ICONS[i.status]}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{i.alertTitle}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-[#2a2a3e] text-school-muted capitalize">{i.status}</span>
                </div>
                <div className="text-xs text-school-muted mt-0.5">Student: {i.studentName}</div>
                <div className="text-xs text-school-muted mt-0.5">Action: {i.actionTaken}</div>
                {i.followupDate && <div className="text-[10px] text-amber-600 mt-1">Follow-up: {new Date(i.followupDate).toLocaleDateString()}</div>}
                {i.remarks && <div className="text-xs text-school-muted mt-1 italic">{i.remarks}</div>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InterventionsTab;
