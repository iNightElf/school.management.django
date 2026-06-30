import { useState } from 'react';
import { api } from '../../store';
import Toast, { toast } from '../../components/Toast';
import { Loader2, X, Check } from 'lucide-react';

interface Period {
  id: string;
  subject_name: string;
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

interface Props {
  period: Period;
  weekStart: string;
  onSave: () => void;
  onClose: () => void;
}

export default function LessonPlanModal({ period, weekStart, onSave, onClose }: Props) {
  const existing = period.lesson_plan;
  const [topic, setTopic] = useState(existing?.topic || '');
  const [objectives, setObjectives] = useState(existing?.learning_objectives || '');
  const [activities, setActivities] = useState(existing?.activities || '');
  const [materials, setMaterials] = useState(existing?.materials || '');
  const [assessment, setAssessment] = useState(existing?.assessment || '');
  const [remarks, setRemarks] = useState(existing?.remarks || '');
  const [completed, setCompleted] = useState(existing?.completed || false);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!topic.trim()) { toast('Topic is required', 'error'); return; }
    setSaving(true);
    try {
      await api.post('/teacher/routine/lesson_plan/', {
        routine_template: period.id,
        week_start: weekStart,
        topic,
        learning_objectives: objectives,
        activities,
        materials,
        assessment,
        remarks,
        completed,
      });
      toast('Lesson plan saved', 'success');
      onSave();
    } catch (e: any) {
      toast(e.response?.data?.error || 'Failed to save', 'error');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-[#1a1a2e] rounded-t-2xl sm:rounded-2xl w-full sm:max-w-lg max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-white dark:bg-[#1a1a2e] border-b border-school-border dark:border-[#2a2a3e] px-5 py-3 flex items-center justify-between z-10">
          <div>
            <h2 className="font-bold text-sm text-school-primary dark:text-[#e0e0e8]">{period.subject_name}</h2>
            <p className="text-[10px] text-school-muted">Lesson Plan · Week starting {weekStart}</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-school-paper dark:hover:bg-white/5 rounded-full transition-colors">
            <X size={18} className="text-school-muted" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Topic *</label>
            <input
              type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8]"
              placeholder="Lesson topic"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Learning Objectives</label>
            <textarea
              value={objectives} onChange={(e) => setObjectives(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] resize-none"
              placeholder="What students will learn"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Teaching Activities</label>
            <textarea
              value={activities} onChange={(e) => setActivities(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] resize-none"
              placeholder="Activities and methods"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Teaching Materials</label>
            <input
              type="text" value={materials} onChange={(e) => setMaterials(e.target.value)}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8]"
              placeholder="Materials needed"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Assessment</label>
            <textarea
              value={assessment} onChange={(e) => setAssessment(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] resize-none"
              placeholder="How learning will be assessed"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase text-school-muted tracking-wider block mb-1">Remarks</label>
            <textarea
              value={remarks} onChange={(e) => setRemarks(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm focus:outline-none focus:border-school-accent bg-school-paper dark:bg-[#2a2a3e] text-school-primary dark:text-[#e0e0e8] resize-none"
              placeholder="Additional notes"
            />
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <div
              onClick={() => setCompleted(!completed)}
              className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${
                completed ? 'bg-green-500 border-green-500' : 'border-school-border'
              }`}
            >
              {completed && <Check size={14} className="text-white" />}
            </div>
            <span className="text-xs font-semibold text-school-primary dark:text-[#e0e0e8]">Mark as completed</span>
          </label>

          <button
            onClick={handleSave}
            disabled={saving || !topic.trim()}
            className="w-full px-4 py-3 bg-school-accent text-white rounded-xl text-sm font-bold hover:bg-school-accent/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? <Loader2 size={18} className="animate-spin" /> : null}
            {saving ? 'Saving...' : 'Save Lesson Plan'}
          </button>
        </div>
      </div>
      <Toast />
    </div>
  );
}
