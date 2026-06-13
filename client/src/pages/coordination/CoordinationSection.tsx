import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useUIStore } from '../../store';
import CoordinationDashboard from './CoordinationDashboard';
import AlertsTab from './AlertsTab';
import InterventionsTab from './InterventionsTab';
import WeeklyReportsTab from './WeeklyReportsTab';
import ClassTestsTab from './ClassTestsTab';
import CoordinatorTasksTab from './CoordinatorTasksTab';
import ParentCommsTab from './ParentCommsTab';
import { LayoutDashboard, AlertTriangle, Stethoscope, ClipboardList, FileText, ListTodo, Phone } from 'lucide-react';

type Tab = 'dashboard' | 'alerts' | 'interventions' | 'reports' | 'tests' | 'tasks' | 'comms';

const TABS: { key: Tab; label: string; icon: ReactNode }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={14} /> },
  { key: 'alerts', label: 'Alerts', icon: <AlertTriangle size={14} /> },
  { key: 'interventions', label: 'Interventions', icon: <Stethoscope size={14} /> },
  { key: 'reports', label: 'Weekly Reports', icon: <ClipboardList size={14} /> },
  { key: 'tests', label: 'Class Tests', icon: <FileText size={14} /> },
  { key: 'tasks', label: 'Tasks', icon: <ListTodo size={14} /> },
  { key: 'comms', label: 'Parent Comms', icon: <Phone size={14} /> },
];

const CoordinationSection = () => {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  useEffect(() => { document.title = 'Coordination Hub - AL RAWA English School'; }, []);
  useEffect(() => { useUIStore.getState().registerSwipeBack(() => setActiveTab('dashboard')); }, []);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === t.key ? 'bg-school-primary text-white shadow-lg' : 'bg-white border border-school-border hover:border-school-accent'}`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' && <CoordinationDashboard />}
      {activeTab === 'alerts' && <AlertsTab />}
      {activeTab === 'interventions' && <InterventionsTab />}
      {activeTab === 'reports' && <WeeklyReportsTab />}
      {activeTab === 'tests' && <ClassTestsTab />}
      {activeTab === 'tasks' && <CoordinatorTasksTab />}
      {activeTab === 'comms' && <ParentCommsTab />}
    </div>
  );
};

export default CoordinationSection;
