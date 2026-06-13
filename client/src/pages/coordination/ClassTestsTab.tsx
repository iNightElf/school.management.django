import { useEffect, useState } from 'react';
import { useSchoolStore } from '../../store';
import { Plus, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { TERM_NAMES } from '../../lib/config';
import { toast } from '../../components/Toast';
import type { ClassTest } from '../../lib/types';

const TERM_OPTIONS = [
  { value: '1', label: TERM_NAMES['1'] },
  { value: '2', label: TERM_NAMES['2'] },
  { value: '3', label: TERM_NAMES['3'] },
];

const ClassTestsTab = () => {
  const { classTests, fetchClassTests, createClassTest, bulkMarks, classes, fetchClasses, subjects, fetchSubjects, students, fetchStudents, subjectAverages, fetchSubjectAverages } = useSchoolStore();
  const [showForm, setShowForm] = useState(false);
  const [selectedTest, setSelectedTest] = useState<ClassTest | null>(null);
  const [classFilter, setClassFilter] = useState('');
  const [termFilter, setTermFilter] = useState('1');
  const [form, setForm] = useState({ schoolClass: '', subject: '', term: '1', testName: '', testDate: '', totalMarks: 100 });
  const [marksData, setMarksData] = useState<Record<string, number>>({});
  const [showAverages, setShowAverages] = useState(false);
  const [creating, setCreating] = useState(false);
  const [savingMarks, setSavingMarks] = useState(false);

  useEffect(() => { fetchClassTests(); fetchClasses(); }, []);

  const filtered = classTests.filter(t => {
    if (classFilter && t.schoolClass !== classFilter) return false;
    if (termFilter && t.term !== termFilter) return false;
    return true;
  });

  const handleClassChange = async (classId: string) => {
    setForm(f => ({ ...f, schoolClass: classId, subject: '' }));
    if (classId) await fetchSubjects(classId);
  };

  const handleCreateTest = async () => {
    if (!form.schoolClass || !form.subject || !form.testName || !form.testDate) return toast('All fields are required', 'error');
    setCreating(true);
    try {
      await createClassTest(form);
      toast('Class test created', 'success');
      setForm({ schoolClass: '', subject: '', term: '1', testName: '', testDate: '', totalMarks: 100 });
      setShowForm(false);
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Failed to create test', 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleSelectTest = async (test: ClassTest) => {
    if (selectedTest?.id === test.id) { setSelectedTest(null); return; }
    setSelectedTest(test);
    await fetchStudents({ class_id: test.schoolClass });
    const marksMap: Record<string, number> = {};
    (test.marks || []).forEach(m => { marksMap[m.student] = m.marksObtained; });
    setMarksData(marksMap);
  };

  const handleSaveMarks = async () => {
    if (!selectedTest) return;
    setSavingMarks(true);
    try {
      const marks = Object.entries(marksData).map(([studentId, marksObtained]) => ({ studentId, marksObtained }));
      await bulkMarks(selectedTest.id, marks);
      toast('Marks saved successfully', 'success');
      setSelectedTest(null);
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Failed to save marks', 'error');
    } finally {
      setSavingMarks(false);
    }
  };

  const handleLoadAverages = async () => {
    if (!classFilter) return;
    await fetchSubjectAverages(classFilter, termFilter);
    setShowAverages(true);
  };

  const termLabel = (term: string) => TERM_NAMES[term as keyof typeof TERM_NAMES] || term;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-school-primary dark:text-[#e0e0e8]">Class Tests</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors">
          <Plus size={14} /> New Test
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-2">
        <select value={classFilter} onChange={e => setClassFilter(e.target.value)}
          className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
          <option value="">All Classes</option>
          {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={termFilter} onChange={e => setTermFilter(e.target.value)}
          className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
          {TERM_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      {/* Subject Averages Button */}
      {classFilter && (
        <button onClick={handleLoadAverages}
          className="w-full px-3 py-2 bg-school-accent text-white text-xs font-bold rounded-lg hover:bg-school-accent/90 transition-colors">
          View Subject Averages ({termLabel(termFilter)}) - 10-Point Scale
        </button>
      )}

      {/* Subject Averages Display */}
      {showAverages && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">Subject Averages ({termLabel(termFilter)})</h3>
            <button onClick={() => setShowAverages(false)} className="text-xs text-school-muted hover:text-school-primary">Hide</button>
          </div>
          {subjectAverages.length === 0 ? (
            <div className="text-center py-4 text-school-muted text-xs">No test data for this class and term</div>
          ) : (
            <div className="space-y-2">
              {subjectAverages.map(s => (
                <div key={s.subjectId} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50 dark:bg-[#2a2a3e]">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-school-primary dark:text-[#e0e0e8] truncate">{s.subjectName}</div>
                    <div className="text-[10px] text-school-muted">{s.totalTests} test(s)</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${s.averageOutOf10 >= 7 ? 'text-green-600' : s.averageOutOf10 >= 5 ? 'text-amber-600' : 'text-red-600'}`}>
                      {s.averageOutOf10.toFixed(1)}
                    </div>
                    <div className="text-[10px] text-school-muted">/10</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Form */}
      {showForm && (
        <div className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <select value={form.schoolClass} onChange={e => handleClassChange(e.target.value)}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="">Select Class</option>
              {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
              <option value="">Select Subject</option>
              {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <select value={form.term} onChange={e => setForm(f => ({ ...f, term: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white">
            {TERM_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <input type="text" placeholder="Test Name" value={form.testName} onChange={e => setForm(f => ({ ...f, testName: e.target.value }))}
            className="w-full px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          <div className="grid grid-cols-2 gap-2">
            <input type="date" value={form.testDate} onChange={e => setForm(f => ({ ...f, testDate: e.target.value }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
            <input type="number" placeholder="Total Marks" value={form.totalMarks} onChange={e => setForm(f => ({ ...f, totalMarks: parseInt(e.target.value) || 100 }))}
              className="px-3 py-2 border border-school-border rounded-lg text-sm dark:bg-[#2a2a3e] dark:text-white" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreateTest} disabled={creating}
              className="flex items-center gap-2 px-4 py-2 bg-school-primary text-white text-sm font-bold rounded-lg hover:bg-school-primary/90 transition-colors disabled:opacity-50">
              {creating && <Loader2 size={14} className="animate-spin" />}
              Create
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-100 text-school-muted text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Test List */}
      <div className="space-y-2">
        {filtered.length === 0 && <div className="text-center py-8 text-school-muted text-sm">No class tests found</div>}
        {filtered.map(test => (
          <div key={test.id} className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] overflow-hidden">
            <button onClick={() => handleSelectTest(test)}
              className="w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-[#2a2a3e] transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">{test.testName}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-school-accent/10 text-school-accent font-semibold">{termLabel(test.term)}</span>
                  </div>
                  <div className="text-xs text-school-muted">{test.className} - {test.subjectName}</div>
                  <div className="text-[10px] text-school-muted mt-0.5">{new Date(test.testDate).toLocaleDateString()} - Total: {test.totalMarks}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-bold text-school-primary dark:text-[#e0e0e8]">Avg: {test.averageMarks ?? 0}</div>
                    <div className="text-[10px] text-school-muted">Pass: {test.passRate ?? 0}%</div>
                  </div>
                  {selectedTest?.id === test.id ? <ChevronUp size={16} className="text-school-muted" /> : <ChevronDown size={16} className="text-school-muted" />}
                </div>
              </div>
            </button>

            {/* Expanded Marks Entry */}
            {selectedTest?.id === test.id && (
              <div className="border-t border-school-border dark:border-[#2a2a3e] p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-school-muted uppercase">Enter Marks</h4>
                  <button onClick={handleSaveMarks} disabled={savingMarks}
                    className="flex items-center gap-2 px-3 py-1.5 bg-school-primary text-white text-xs font-bold rounded-lg hover:bg-school-primary/90 transition-colors disabled:opacity-50">
                    {savingMarks && <Loader2 size={12} className="animate-spin" />}
                    Save All Marks
                  </button>
                </div>
                <div className="space-y-1.5 max-h-64 overflow-y-auto">
                  {students.filter(s => s.classId === test.schoolClass).map(s => (
                    <div key={s.id} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50 dark:bg-[#2a2a3e]">
                      <span className="text-xs text-school-muted w-8">{s.roll}</span>
                      <span className="text-sm text-school-primary dark:text-[#e0e0e8] flex-1 truncate">{s.name}</span>
                      <input type="number" min={0} max={test.totalMarks}
                        value={marksData[s.id] ?? ''}
                        onChange={e => setMarksData(prev => ({ ...prev, [s.id]: parseInt(e.target.value) || 0 }))}
                        className="w-20 px-2 py-1 border border-school-border rounded text-sm text-right dark:bg-[#1a1a2e] dark:text-white" />
                      <span className="text-[10px] text-school-muted w-8 text-right">
                        {marksData[s.id] != null ? Math.round(marksData[s.id] / test.totalMarks * 100) : 0}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ClassTestsTab;
