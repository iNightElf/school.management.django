import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../store';
import Toast, { toast } from '../../components/Toast';
import ParentLayout from './ParentLayout';
import { ChevronLeft, BarChart3 } from 'lucide-react';
import { TERM_NAMES } from '../../lib/config';

interface Result {
  id: string;
  session: string;
  term: string;
  marks: Record<string, number>;
  comment: string | null;
  createdAt: string;
}

export default function ParentResults() {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState('');

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    api.get(`/parents/results/${studentId}/`, { params: { session: selectedSession || undefined } })
      .then((res) => setResults(res.data))
      .catch(() => toast('Failed to load results', 'error'))
      .finally(() => setLoading(false));
  }, [studentId, selectedSession]);

  const sessions = [...new Set(results.map((r) => r.session))];

  return (
    <ParentLayout>
      <Toast />
      {!studentId ? (
        <StudentSelector onSelect={(id) => navigate(`/parent/results/${id}`)} />
      ) : (
        <>
          <button onClick={() => navigate('/parent')} className="flex items-center gap-1 text-sm text-school-muted mb-3 hover:text-school-primary">
            <ChevronLeft size={16} />
            Back to Dashboard
          </button>

          {loading ? (
            <div className="animate-pulse bg-white rounded-xl p-6 border border-school-border">
              <div className="h-6 bg-gray-200 rounded w-1/2 mb-4" />
              {[1, 2].map((i) => <div key={i} className="h-20 bg-gray-100 rounded mb-2" />)}
            </div>
          ) : results.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center border border-school-border">
              <BarChart3 size={40} className="mx-auto text-school-muted mb-3" />
              <p className="text-school-muted font-medium">No results available yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.length > 1 && (
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedSession('')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      !selectedSession ? 'bg-school-primary text-white' : 'bg-gray-100 text-school-muted'
                    }`}
                  >
                    All
                  </button>
                  {sessions.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSelectedSession(s)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                        selectedSession === s ? 'bg-school-primary text-white' : 'bg-gray-100 text-school-muted'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {results.map((r) => {
                const entries = Object.entries(r.marks || {});
                const total = entries.reduce((sum, [, val]) => sum + (typeof val === 'number' ? val : 0), 0);
                return (
                  <div key={r.id} className="bg-white rounded-xl border border-school-border overflow-hidden">
                    <div className="px-4 py-3 bg-gray-50 border-b border-school-border flex items-center justify-between">
                      <div>
                        <span className="font-bold text-sm text-school-primary">{TERM_NAMES[r.term] || `Term ${r.term}`}</span>
                        <span className="text-xs text-school-muted ml-2">{r.session}</span>
                      </div>
                      <span className="text-xs text-school-muted">{new Date(r.createdAt).toLocaleDateString()}</span>
                    </div>
                    <div className="divide-y divide-school-border">
                      {entries.map(([subject, score]) => (
                        <div key={subject} className="px-4 py-2.5 flex items-center justify-between">
                          <span className="text-sm text-school-primary">{subject}</span>
                          <span className="font-semibold text-sm">{score}</span>
                        </div>
                      ))}
                      <div className="px-4 py-2.5 flex items-center justify-between bg-gray-50">
                        <span className="text-sm font-bold text-school-primary">Total</span>
                        <span className="font-bold text-school-primary">{total}</span>
                      </div>
                    </div>
                    {r.comment && (
                      <div className="px-4 py-2 text-xs text-school-muted border-t border-school-border italic">
                        {r.comment}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </ParentLayout>
  );
}

function StudentSelector({ onSelect }: { onSelect: (id: string) => void }) {
  const [students, setStudents] = useState<Array<{ id: string; name: string; klass: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/parents/my-students/')
      .then((res) => setStudents(res.data))
      .catch(() => toast('Failed to load students', 'error'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-3">
      <h2 className="font-serif text-lg text-school-primary">Select a student</h2>
      {loading ? (
        <div className="text-school-muted">Loading...</div>
      ) : (
        students.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className="w-full bg-white rounded-xl border border-school-border p-4 text-left card-shadow hover:shadow-md transition-shadow"
          >
            <p className="font-bold text-school-primary">{s.name}</p>
            <p className="text-xs text-school-muted">{s.klass}</p>
          </button>
        ))
      )}
    </div>
  );
}
