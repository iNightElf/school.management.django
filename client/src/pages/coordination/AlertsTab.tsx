import { useEffect, useState } from 'react';
import { useSchoolStore } from '../../store';
import { Plus, CheckCircle, AlertTriangle, Clock, Loader2 } from 'lucide-react';
import { toast } from '../../components/Toast';

const SEVERITY_COLORS = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  low: 'bg-blue-100 text-blue-700 border-blue-200',
};
const STATUS_ICONS = {
  open: <AlertTriangle size={14} className="text-red-500" />,
  pending: <Clock size={14} className="text-amber-500" />,
  resolved: <CheckCircle size={14} className="text-green-500" />,
};

const AlertsTab = () => {
  const { alerts, fetchAlerts, createAlert, resolveAlert, students, fetchStudents } = useSchoolStore();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [form, setForm] = useState({ student: '', alertType: 'attendance', title: '', description: '', severity: 'medium' });
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchAlerts(); fetchStudents(); }, []);

  const filtered = filter === 'all' ? alerts : alerts.filter(a => a.status === filter);

  const handleSubmit = async () => {
    if (!form.student || !form.title) return toast('Student and title are required', 'error');
    setSaving(true);
    try {
      await createAlert(form);
      toast('Alert created successfully', 'success');
      setForm({ student: '', alertType: 'attendance', title: '', description: '', severity: 'medium' });
      setShowForm(false);
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Failed to create alert', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await resolveAlert(id);
      toast('Alert resolved', 'success');
    } catch {
      toast('Failed to resolve alert', 'error');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Alerts</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors">
          <Plus size={14} /> New Alert
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'open', 'pending', 'resolved'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-colors ${filter === s ? 'bg-school-primary text-white' : 'bg-white border border-school-border text-school-muted hover:border-school-accent'}`}>
            {s}
          </button>
        ))}
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <select value={form.student} onChange={e => setForm(f => ({ ...f, student: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
            <option value="">Select Student</option>
            {students.map(s => (
              <option key={s.id} value={s.id}>{s.name} ({s.class})</option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-2">
            <select value={form.alertType} onChange={e => setForm(f => ({ ...f, alertType: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="attendance">Attendance</option>
              <option value="academic">Academic</option>
              <option value="behavior">Behavior</option>
              <option value="parent">Parent</option>
            </select>
            <select value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <input type="text" placeholder="Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          <textarea placeholder="Description (optional)" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" rows={2} />
          <div className="flex gap-2">
            <button onClick={handleSubmit} disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-school-primary text-white text-sm font-bold rounded-lg hover:bg-school-primary/90 transition-colors disabled:opacity-50">
              {saving && <Loader2 size={14} className="animate-spin" />}
              Save
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-100 text-school-muted text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Alert List */}
      <div className="space-y-2">
        {filtered.length === 0 && (
          <div className="text-center py-8 text-school-muted text-sm">No alerts found</div>
        )}
        {filtered.map(alert => (
          <div key={alert.id} className={`bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 ${alert.status === 'resolved' ? 'opacity-60' : ''}`}>
            <div className="flex items-start gap-3">
              <div className="mt-0.5">{STATUS_ICONS[alert.status as keyof typeof STATUS_ICONS]}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{alert.title}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${SEVERITY_COLORS[alert.severity as keyof typeof SEVERITY_COLORS]}`}>
                    {alert.severity}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-[#2a2a3e] text-school-muted capitalize">
                    {alert.alertType}
                  </span>
                </div>
                <div className="text-xs text-school-muted mt-0.5">{alert.studentName} - {alert.className}</div>
                {alert.description && <div className="text-xs text-school-muted mt-1">{alert.description}</div>}
                <div className="text-[10px] text-school-muted mt-1">by {alert.createdByName} - {new Date(alert.createdAt).toLocaleDateString()}</div>
              </div>
              {alert.status !== 'resolved' && (
                <button onClick={() => handleResolve(alert.id)}
                  className="px-2 py-1 bg-green-50 text-green-600 text-[10px] font-bold rounded-lg hover:bg-green-100 transition-colors flex-shrink-0">
                  Resolve
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsTab;
