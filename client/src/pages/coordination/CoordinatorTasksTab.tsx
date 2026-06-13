import { useEffect, useState } from 'react';
import { useSchoolStore } from '../../store';
import { Plus, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

const PRIORITY_COLORS = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  low: 'bg-blue-100 text-blue-700 border-blue-200',
};

const CoordinatorTasksTab = () => {
  const { coordinatorTasks, fetchCoordinatorTasks, createCoordinatorTask, completeCoordinatorTask } = useSchoolStore();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [form, setForm] = useState({ title: '', description: '', dueDate: '', priority: 'medium', status: 'pending' });

  useEffect(() => { fetchCoordinatorTasks(); }, []);

  const filtered = filter === 'all' ? coordinatorTasks : coordinatorTasks.filter(t => t.status === filter);

  const handleSubmit = async () => {
    if (!form.title) return;
    await createCoordinatorTask(form);
    setForm({ title: '', description: '', dueDate: '', priority: 'medium', status: 'pending' });
    setShowForm(false);
  };

  const handleComplete = async (id: string) => {
    await completeCoordinatorTask(id);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Coordinator Tasks</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors">
          <Plus size={14} /> New Task
        </button>
      </div>

      <div className="flex gap-2">
        {['all', 'pending', 'in_progress', 'completed'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-colors ${filter === s ? 'bg-school-primary text-white' : 'bg-white border border-school-border text-school-muted hover:border-school-accent'}`}>
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {showForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <input type="text" placeholder="Task Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          <textarea placeholder="Description (optional)" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" rows={2} />
          <div className="grid grid-cols-2 gap-2">
            <input type="date" value={form.dueDate} onChange={e => setForm(f => ({ ...f, dueDate: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
            <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={handleSubmit} className="px-4 py-2 bg-school-primary text-white text-sm font-bold rounded-lg hover:bg-school-primary/90 transition-colors">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-100 text-school-muted text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {filtered.length === 0 && <div className="text-center py-8 text-school-muted text-sm">No tasks found</div>}
        {filtered.map(task => (
          <div key={task.id} className={`bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 ${task.status === 'completed' ? 'opacity-60' : ''}`}>
            <div className="flex items-start gap-3">
              {task.status === 'completed' ? (
                <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
              ) : task.status === 'in_progress' ? (
                <Clock size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
              ) : (
                <AlertTriangle size={16} className="text-school-muted mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{task.title}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${PRIORITY_COLORS[task.priority]}`}>{task.priority}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-[#2a2a3e] text-school-muted capitalize">{task.status.replace('_', ' ')}</span>
                </div>
                {task.description && <div className="text-xs text-school-muted mt-1">{task.description}</div>}
                {task.dueDate && <div className="text-[10px] text-amber-600 mt-1">Due: {new Date(task.dueDate).toLocaleDateString()}</div>}
                {task.relatedAlertTitle && <div className="text-[10px] text-school-muted mt-0.5">Alert: {task.relatedAlertTitle}</div>}
              </div>
              {task.status !== 'completed' && (
                <button onClick={() => handleComplete(task.id)}
                  className="px-2 py-1 bg-green-50 text-green-600 text-[10px] font-bold rounded-lg hover:bg-green-100 transition-colors flex-shrink-0">
                  Done
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CoordinatorTasksTab;
