import { useEffect } from 'react';
import { useSchoolStore } from '../../store';
import { AlertTriangle, CheckCircle, Clock, ListTodo, FileText, Phone } from 'lucide-react';
import { TERM_NAMES } from '../../lib/config';

const CoordinationDashboard = () => {
  const { coordinationDashboard, fetchCoordinationDashboard } = useSchoolStore();

  useEffect(() => { fetchCoordinationDashboard(); }, []);

  const d = coordinationDashboard;

  return (
    <div className="space-y-4">
      <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Coordination Dashboard</h2>

      {/* Alert Status Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-red-500" />
            <span className="text-xs font-bold text-red-600 uppercase">Urgent</span>
          </div>
          <div className="text-2xl font-bold text-red-700 dark:text-red-400">{d?.alertsByStatus.open ?? 0}</div>
          <div className="text-[10px] text-red-500 mt-0.5">Open Alerts</div>
        </div>

        <div className="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={16} className="text-amber-500" />
            <span className="text-xs font-bold text-amber-600 uppercase">Attention</span>
          </div>
          <div className="text-2xl font-bold text-amber-700 dark:text-amber-400">{d?.alertsByStatus.pending ?? 0}</div>
          <div className="text-[10px] text-amber-500 mt-0.5">Pending Alerts</div>
        </div>

        <div className="bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={16} className="text-green-500" />
            <span className="text-xs font-bold text-green-600 uppercase">Resolved</span>
          </div>
          <div className="text-2xl font-bold text-green-700 dark:text-green-400">{d?.alertsByStatus.resolved ?? 0}</div>
          <div className="text-[10px] text-green-500 mt-0.5">Resolved Alerts</div>
        </div>
      </div>

      {/* Alert Types */}
      <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
        <h3 className="text-sm font-bold text-school-primary dark:text-[#e0e0e8] mb-3">Alerts by Type</h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Attendance', count: d?.alertsByType.attendance ?? 0, color: 'bg-blue-500' },
            { label: 'Academic', count: d?.alertsByType.academic ?? 0, color: 'bg-purple-500' },
            { label: 'Behavior', count: d?.alertsByType.behavior ?? 0, color: 'bg-orange-500' },
            { label: 'Parent', count: d?.alertsByType.parent ?? 0, color: 'bg-pink-500' },
          ].map(t => (
            <div key={t.label} className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-[#2a2a3e]">
              <div className={`w-2 h-2 rounded-full ${t.color}`} />
              <span className="text-xs font-semibold text-school-muted">{t.label}</span>
              <span className="ml-auto text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{t.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white dark:bg-[#1a1a2e] border border-school-border dark:border-[#2a2a3e] rounded-xl p-3 text-center">
          <ListTodo size={20} className="mx-auto text-school-primary mb-1" />
          <div className="text-lg font-bold text-school-primary dark:text-[#e0e0e8]">{d?.pendingTasks ?? 0}</div>
          <div className="text-[10px] text-school-muted">Pending Tasks</div>
        </div>
        <div className="bg-white dark:bg-[#1a1a2e] border border-school-border dark:border-[#2a2a3e] rounded-xl p-3 text-center">
          <FileText size={20} className="mx-auto text-school-primary mb-1" />
          <div className="text-lg font-bold text-school-primary dark:text-[#e0e0e8]">{d?.pendingReports ?? 0}</div>
          <div className="text-[10px] text-school-muted">Pending Reports</div>
        </div>
        <div className="bg-white dark:bg-[#1a1a2e] border border-school-border dark:border-[#2a2a3e] rounded-xl p-3 text-center">
          <Phone size={20} className="mx-auto text-school-primary mb-1" />
          <div className="text-lg font-bold text-school-primary dark:text-[#e0e0e8]">{d?.upcomingFollowups ?? 0}</div>
          <div className="text-[10px] text-school-muted">Upcoming Follow-ups</div>
        </div>
      </div>

      {/* Recent Class Tests */}
      {d?.recentTests && d.recentTests.length > 0 && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
          <h3 className="text-sm font-bold text-school-primary dark:text-[#e0e0e8] mb-3">Recent Class Tests</h3>
          <div className="space-y-2">
            {d.recentTests.map(t => (
              <div key={t.id} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50 dark:bg-[#2a2a3e]">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-school-primary dark:text-[#e0e0e8] truncate">{t.testName}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-school-accent/10 text-school-accent font-semibold">{TERM_NAMES[t.term as keyof typeof TERM_NAMES] || t.term}</span>
                  </div>
                  <div className="text-[10px] text-school-muted">{t.className} - {t.subjectName}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{t.averageMarks}/{t.totalMarks}</div>
                  <div className="text-[10px] text-school-muted">{t.studentCount} students</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoordinationDashboard;
