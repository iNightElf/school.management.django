import { useEffect, useState } from 'react';
import { useSchoolStore, useAuthStore } from '../../store';
import { Plus, Send } from 'lucide-react';

const WeeklyReportsTab = () => {
  const { weeklyReports, fetchWeeklyReports, createWeeklyReport, submitWeeklyReport, teachers, fetchTeachers } = useSchoolStore();
  const user = useAuthStore(s => s.user);
  const isAdmin = user?.role === 'admin';
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    classTeacher: '', weekStartDate: '',
    attendanceNotes: '', academicsNotes: '', behaviorNotes: '', parentIssuesNotes: '', recognitionNotes: '',
  });

  useEffect(() => { fetchWeeklyReports(); fetchTeachers(); }, []);

  const handleSubmit = async () => {
    if (!form.classTeacher || !form.weekStartDate) return;
    await createWeeklyReport(form);
    setForm({ classTeacher: '', weekStartDate: '', attendanceNotes: '', academicsNotes: '', behaviorNotes: '', parentIssuesNotes: '', recognitionNotes: '' });
    setShowForm(false);
  };

  const handleSubmitReport = async (id: string) => {
    await submitWeeklyReport(id);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Weekly Reports</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors">
          <Plus size={14} /> New Report
        </button>
      </div>

      {showForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <select value={form.classTeacher} onChange={e => setForm(f => ({ ...f, classTeacher: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="">Select Class Teacher</option>
              {teachers.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
            <input type="date" value={form.weekStartDate} onChange={e => setForm(f => ({ ...f, weekStartDate: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          </div>
          {[
            { key: 'attendanceNotes', label: 'Attendance' },
            { key: 'academicsNotes', label: 'Academics' },
            { key: 'behaviorNotes', label: 'Behavior' },
            { key: 'parentIssuesNotes', label: 'Parent Issues' },
            { key: 'recognitionNotes', label: 'Recognition' },
          ].map(f => (
            <textarea key={f.key} placeholder={f.label} value={(form as any)[f.key]}
              onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
              className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" rows={2} />
          ))}
          <div className="flex gap-2">
            <button onClick={handleSubmit} className="px-4 py-2 bg-school-primary text-white text-sm font-bold rounded-lg hover:bg-school-primary/90 transition-colors">Save Draft</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-100 text-school-muted text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {weeklyReports.length === 0 && <div className="text-center py-8 text-school-muted text-sm">No reports found</div>}
        {weeklyReports.map(r => (
          <div key={r.id} className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{r.teacherName}</span>
                  <span className="text-xs text-school-muted">- {r.className}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${r.status === 'submitted' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                    {r.status}
                  </span>
                </div>
                <div className="text-[10px] text-school-muted mt-0.5">Week of {new Date(r.weekStartDate).toLocaleDateString()}</div>
              </div>
              {isAdmin && r.status === 'draft' && (
                <button onClick={() => handleSubmitReport(r.id)}
                  className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-600 text-[10px] font-bold rounded-lg hover:bg-green-100 transition-colors">
                  <Send size={10} /> Submit
                </button>
              )}
            </div>
            {r.attendanceNotes && <div className="text-xs text-school-muted mt-2"><strong>Attendance:</strong> {r.attendanceNotes}</div>}
            {r.academicsNotes && <div className="text-xs text-school-muted mt-1"><strong>Academics:</strong> {r.academicsNotes}</div>}
            {r.behaviorNotes && <div className="text-xs text-school-muted mt-1"><strong>Behavior:</strong> {r.behaviorNotes}</div>}
            {r.parentIssuesNotes && <div className="text-xs text-school-muted mt-1"><strong>Parent Issues:</strong> {r.parentIssuesNotes}</div>}
            {r.recognitionNotes && <div className="text-xs text-green-600 mt-1"><strong>Recognition:</strong> {r.recognitionNotes}</div>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeeklyReportsTab;
