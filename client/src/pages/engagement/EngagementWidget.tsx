import { useState, useEffect } from 'react';
import { api } from '../../store';
import { toast } from '../../components/Toast';
import { Brain, Lightbulb, SmilePlus, Target, BookOpen, Flame } from 'lucide-react';

const MOODS = [
  { value: 1, emoji: '😢', label: 'Terrible' },
  { value: 2, emoji: '😟', label: 'Bad' },
  { value: 3, emoji: '😐', label: 'Okay' },
  { value: 4, emoji: '😊', label: 'Good' },
  { value: 5, emoji: '😄', label: 'Great' },
];

export default function EngagementWidget({ onOpenPanel }: { onOpenPanel: (panel: string) => void }) {
  const [streak, setStreak] = useState<any>(null);
  const [quizDone, setQuizDone] = useState(false);
  const [riddleDone, setRiddleDone] = useState(false);
  const [moodDone, setMoodDone] = useState(false);

  const loadData = async () => {
    try {
      const [streakRes, quizRes, riddleRes, moodRes] = await Promise.all([
        api.get('/engagement/streak/me/'),
        api.get('/engagement/quiz/today/'),
        api.get('/engagement/riddle/today/'),
        api.get('/engagement/mood/history/', { params: { days: 1 } }),
      ]);
      setStreak(streakRes.data);
      setQuizDone(quizRes.data?.hasResponded || false);
      setRiddleDone(riddleRes.data?.hasResponded || false);
      const moodData = moodRes.data;
      setMoodDone(Array.isArray(moodData) && moodData.length > 0);
    } catch { /* ignore */ }
  };

  useEffect(() => { loadData(); }, []);

  const cards = [
    { key: 'quiz', icon: <Brain size={20} />, label: 'Quiz', sub: quizDone ? 'Done today' : 'Play now', color: 'from-purple-500 to-purple-600', ring: 'ring-purple-200' },
    { key: 'riddle', icon: <Lightbulb size={20} />, label: 'Riddle', sub: riddleDone ? 'Done today' : 'Guess now', color: 'from-amber-500 to-amber-600', ring: 'ring-amber-200' },
    { key: 'mood', icon: <SmilePlus size={20} />, label: 'Mood', sub: moodDone ? 'Checked in' : 'How are you?', color: 'from-emerald-500 to-emerald-600', ring: 'ring-emerald-200' },
    { key: 'challenge', icon: <Target size={20} />, label: 'Challenge', sub: 'Weekly fun', color: 'from-rose-500 to-rose-600', ring: 'ring-rose-200' },
    { key: 'tips', icon: <BookOpen size={20} />, label: 'Tips', sub: 'Daily wisdom', color: 'from-blue-500 to-blue-600', ring: 'ring-blue-200' },
    { key: 'planner', icon: <BookOpen size={20} />, label: 'Planner', sub: 'Plan today', color: 'from-indigo-500 to-indigo-600', ring: 'ring-indigo-200' },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-serif text-sm text-school-primary">Today's Activities</h3>
        {streak && streak.currentStreak > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 bg-orange-50 border border-orange-200 rounded-full">
            <Flame size={12} className="text-orange-500" />
            <span className="text-[10px] font-bold text-orange-600">{streak.currentStreak}-day streak!</span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {cards.map((c) => (
          <button
            key={c.key}
            onClick={() => onOpenPanel(c.key)}
            className={`bg-gradient-to-br ${c.color} text-white p-3 rounded-xl text-center shadow-sm hover:shadow-md transition-all hover:scale-[1.02] ring-1 ${c.ring}`}
          >
            <div className="flex justify-center mb-1">{c.icon}</div>
            <div className="text-[10px] font-bold">{c.label}</div>
            <div className="text-[8px] opacity-80">{c.sub}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export function QuizPanel({ onClose }: { onClose: () => void }) {
  const [quiz, setQuiz] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [tab, setTab] = useState<'quiz' | 'leaderboard'>('quiz');

  const loadQuiz = async () => {
    setLoading(true);
    try {
      const res = await api.get('/engagement/quiz/today/');
      setQuiz(res.data);
    } catch { toast('Failed to load quiz', 'error'); }
    setLoading(false);
  };

  const submitAnswer = async () => {
    if (!selected) return;
    setSubmitting(true);
    try {
      const res = await api.post('/engagement/quiz/answer/', { selectedAnswer: selected });
      setResult(res.data);
      setQuiz((q: any) => ({ ...q, hasResponded: true }));
    } catch (e: any) {
      toast(e.response?.data?.error || 'Error', 'error');
    }
    setSubmitting(false);
  };

  const loadLeaderboard = async () => {
    try {
      const res = await api.get('/engagement/quiz/leaderboard/');
      setLeaderboard(res.data);
    } catch { /* ignore */ }
  };

  useEffect(() => { loadQuiz(); }, []);
  useEffect(() => { if (tab === 'leaderboard') loadLeaderboard(); }, [tab]);

  if (loading) return <div className="p-6 text-center text-school-muted">Loading...</div>;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-white border-b border-school-border p-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="font-bold text-school-primary">Daily Quiz</h3>
          <div className="flex gap-1">
            <button onClick={() => setTab('quiz')} className={`px-3 py-1 rounded-lg text-xs font-medium ${tab === 'quiz' ? 'bg-purple-100 text-purple-700' : 'text-school-muted'}`}>Quiz</button>
            <button onClick={() => setTab('leaderboard')} className={`px-3 py-1 rounded-lg text-xs font-medium ${tab === 'leaderboard' ? 'bg-purple-100 text-purple-700' : 'text-school-muted'}`}>Leaderboard</button>
            <button onClick={onClose} className="ml-2 px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
          </div>
        </div>

        <div className="p-4">
          {tab === 'quiz' && quiz && (
            <>
              <div className="text-[10px] uppercase tracking-widest text-school-muted font-bold mb-2">{quiz.category}</div>
              <p className="text-sm font-medium text-school-primary mb-4">{quiz.question}</p>

              {!quiz.hasResponded && !result ? (
                <>
                  <div className="space-y-2">
                    {[
                      { key: 'a', text: quiz.option_a },
                      { key: 'b', text: quiz.option_b },
                      { key: 'c', text: quiz.option_c },
                      { key: 'd', text: quiz.option_d },
                    ].map((opt) => (
                      <button
                        key={opt.key}
                        onClick={() => setSelected(opt.key)}
                        className={`w-full text-left p-3 rounded-xl border text-sm transition-all ${
                          selected === opt.key
                            ? 'border-purple-400 bg-purple-50 text-purple-700'
                            : 'border-school-border hover:border-purple-200'
                        }`}
                      >
                        <span className="font-bold mr-2">{opt.key.toUpperCase()}.</span> {opt.text}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={submitAnswer}
                    disabled={!selected || submitting}
                    className="w-full mt-4 py-2.5 bg-purple-600 text-white rounded-xl text-sm font-bold disabled:opacity-50"
                  >
                    {submitting ? 'Submitting...' : 'Submit Answer'}
                  </button>
                </>
              ) : (
                <div className={`p-4 rounded-xl ${result?.isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="text-lg font-bold mb-1">{result?.isCorrect ? 'Correct!' : 'Not quite'}</div>
                  <div className="text-sm text-school-muted">Answer: <span className="font-bold">{result?.correctAnswer?.toUpperCase()}</span></div>
                  {quiz.explanation && <div className="text-xs text-school-muted mt-2">{quiz.explanation}</div>}
                </div>
              )}
            </>
          )}

          {tab === 'leaderboard' && (
            <div className="space-y-2">
              {leaderboard.length === 0 && <p className="text-sm text-school-muted text-center py-4">No responses yet this week</p>}
              {leaderboard.map((entry: any, i: number) => (
                <div key={entry.userId} className="flex items-center gap-3 p-2 rounded-lg hover:bg-school-paper">
                  <span className="text-sm font-bold text-school-muted w-6">{i + 1}</span>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{entry.userName}</div>
                    <div className="text-[10px] text-school-muted">{entry.correctAnswers}/{entry.totalAnswers} correct ({entry.accuracy}%)</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function RiddlePanel({ onClose }: { onClose: () => void }) {
  const [riddle, setRiddle] = useState<any>(null);
  const [guess, setGuess] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showHint, setShowHint] = useState(false);

  const loadRiddle = async () => {
    setLoading(true);
    try {
      const res = await api.get('/engagement/riddle/today/');
      setRiddle(res.data);
    } catch { toast('Failed to load riddle', 'error'); }
    setLoading(false);
  };

  const submitGuess = async () => {
    if (!guess.trim()) return;
    try {
      const res = await api.post('/engagement/riddle/guess/', { guess: guess.trim() });
      setResult(res.data);
      setRiddle((r: any) => ({ ...r, hasResponded: true, showAnswer: true }));
    } catch (e: any) {
      toast(e.response?.data?.error || 'Error', 'error');
    }
  };

  useEffect(() => { loadRiddle(); }, []);

  if (loading) return <div className="p-6 text-center text-school-muted">Loading...</div>;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl">
        <div className="p-4 border-b border-school-border flex items-center justify-between">
          <h3 className="font-bold text-school-primary">Daily Riddle</h3>
          <button onClick={onClose} className="px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
        </div>
        <div className="p-4">
          {riddle && (
            <>
              <p className="text-sm font-medium text-school-primary mb-3">{riddle.question}</p>

              {riddle.hint && !riddle.hasResponded && (
                <button onClick={() => setShowHint(!showHint)} className="text-xs text-amber-600 hover:underline mb-3">
                  {showHint ? 'Hide hint' : 'Show hint'}
                </button>
              )}
              {showHint && <p className="text-xs text-amber-600 mb-3 italic">Hint: {riddle.hint}</p>}

              {!riddle.hasResponded && !result ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={guess}
                    onChange={(e) => setGuess(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitGuess()}
                    placeholder="Your guess..."
                    className="flex-1 px-3 py-2 border border-school-border rounded-xl text-sm"
                  />
                  <button onClick={submitGuess} className="px-4 py-2 bg-amber-500 text-white rounded-xl text-sm font-bold">Guess</button>
                </div>
              ) : (
                <div className={`p-3 rounded-xl ${result?.isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="font-bold text-sm mb-1">{result?.isCorrect ? 'Correct!' : 'Not quite!'}</div>
                  <div className="text-sm">Answer: <span className="font-bold">{riddle.answer || result?.correctAnswer}</span></div>
                  {riddle.yourGuess && !result?.isCorrect && (
                    <div className="text-xs text-school-muted mt-1">Your guess: {riddle.yourGuess}</div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function MoodPanel({ onClose }: { onClose: () => void }) {
  const [selectedMood, setSelectedMood] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const submitMood = async (mood: number) => {
    setSelectedMood(mood);
    setSubmitting(true);
    try {
      await api.post('/engagement/mood/checkin/', { mood });
      setSubmitted(true);
      toast('Mood checked in!', 'success');
    } catch (e: any) {
      toast(e.response?.data?.error || 'Error', 'error');
    }
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm shadow-xl">
        <div className="p-4 border-b border-school-border flex items-center justify-between">
          <h3 className="font-bold text-school-primary">How are you today?</h3>
          <button onClick={onClose} className="px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
        </div>
        <div className="p-6">
          {submitted ? (
            <div className="text-center py-4">
              <div className="text-4xl mb-2">{MOODS.find(m => m.value === selectedMood)?.emoji}</div>
              <p className="text-sm text-school-muted">Thanks for checking in!</p>
            </div>
          ) : (
            <div className="flex justify-center gap-3">
              {MOODS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => submitMood(m.value)}
                  disabled={submitting}
                  className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all hover:scale-110 ${
                    selectedMood === m.value ? 'border-green-400 bg-green-50' : 'border-school-border hover:border-green-200'
                  }`}
                >
                  <span className="text-3xl">{m.emoji}</span>
                  <span className="text-[9px] text-school-muted mt-1">{m.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChallengePanel({ onClose }: { onClose: () => void }) {
  const [challenges, setChallenges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState('');

  const loadChallenges = async () => {
    setLoading(true);
    try {
      const res = await api.get('/engagement/challenges/active/');
      setChallenges(Array.isArray(res.data) ? res.data : []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const respondToChallenge = async (challengeId: string) => {
    if (!response.trim()) return;
    try {
      await api.post(`/engagement/challenges/${challengeId}/respond/`, { textResponse: response.trim() });
      toast('Response submitted!', 'success');
      setResponse('');
      loadChallenges();
    } catch (e: any) {
      toast(e.response?.data?.error || 'Error', 'error');
    }
  };

  useEffect(() => { loadChallenges(); }, []);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-white border-b border-school-border p-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="font-bold text-school-primary">Weekly Challenge</h3>
          <button onClick={onClose} className="px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
        </div>
        <div className="p-4 space-y-4">
          {loading && <p className="text-sm text-school-muted text-center">Loading...</p>}
          {!loading && challenges.length === 0 && (
            <p className="text-sm text-school-muted text-center py-4">No active challenge this week</p>
          )}
          {challenges.map((ch: any) => (
            <div key={ch.id} className="border border-school-border rounded-xl p-4">
              <h4 className="font-bold text-sm text-school-primary">{ch.title}</h4>
              <p className="text-xs text-school-muted mt-1">{ch.description}</p>
              <div className="text-[10px] text-school-muted mt-2">{ch.responseCount} responses</div>
              {!ch.hasResponded ? (
                <div className="mt-3 flex gap-2">
                  <input
                    type="text"
                    value={response}
                    onChange={(e) => setResponse(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && respondToChallenge(ch.id)}
                    placeholder="Your response..."
                    className="flex-1 px-3 py-2 border border-school-border rounded-xl text-sm"
                  />
                  <button onClick={() => respondToChallenge(ch.id)} className="px-4 py-2 bg-rose-500 text-white rounded-xl text-sm font-bold">Send</button>
                </div>
              ) : (
                <div className="mt-2 text-xs text-green-600 font-medium">You participated!</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function TipsPanel({ onClose }: { onClose: () => void }) {
  const [tips, setTips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTips = async () => {
    setLoading(true);
    try {
      const res = await api.get('/engagement/tips/today/');
      setTips(Array.isArray(res.data) ? res.data : []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadTips(); }, []);

  const categoryColors: Record<string, string> = {
    classroom: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    assessment: 'bg-blue-50 border-blue-200 text-blue-700',
    engagement: 'bg-purple-50 border-purple-200 text-purple-700',
    general: 'bg-gray-50 border-gray-200 text-gray-700',
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-white border-b border-school-border p-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="font-bold text-school-primary">Teaching Tips</h3>
          <button onClick={onClose} className="px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
        </div>
        <div className="p-4 space-y-3">
          {loading && <p className="text-sm text-school-muted text-center">Loading...</p>}
          {tips.map((tip: any) => (
            <div key={tip.id} className={`p-3 rounded-xl border ${categoryColors[tip.category] || categoryColors.general}`}>
              <div className="text-[10px] uppercase tracking-widest font-bold mb-1 opacity-70">{tip.category}</div>
              <p className="text-sm">{tip.tip}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function PlannerPanel({ onClose }: { onClose: () => void }) {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ className: '', subject: '', notes: '' });
  const [saving, setSaving] = useState(false);

  const loadPlans = async () => {
    setLoading(true);
    try {
      const res = await api.get('/engagement/lesson-plans/');
      setPlans(Array.isArray(res.data) ? res.data : []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadPlans(); }, []);

  const addPlan = async () => {
    if (!form.className.trim() || !form.subject.trim()) return;
    setSaving(true);
    try {
      const res = await api.post('/engagement/lesson-plans/', {
        className: form.className.trim(),
        subject: form.subject.trim(),
        notes: form.notes.trim(),
      });
      setPlans([...plans, res.data]);
      setForm({ className: '', subject: '', notes: '' });
      toast('Plan added', 'success');
    } catch (e: any) {
      toast(e.response?.data?.error || 'Error', 'error');
    }
    setSaving(false);
  };

  const deletePlan = async (id: string) => {
    try {
      await api.delete(`/engagement/lesson-plans/${id}/`);
      setPlans(plans.filter((p: any) => p.id !== id));
    } catch { /* ignore */ }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-white border-b border-school-border p-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="font-bold text-school-primary">Today's Lesson Plan</h3>
          <button onClick={onClose} className="px-2 py-1 hover:bg-gray-100 rounded-lg text-sm">X</button>
        </div>
        <div className="p-4 space-y-4">
          {loading && <p className="text-sm text-school-muted text-center">Loading...</p>}

          {plans.length > 0 && (
            <div className="space-y-2">
              {plans.map((p: any) => (
                <div key={p.id} className="flex items-start gap-2 p-2 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <div className="flex-1">
                    <div className="text-xs font-bold text-indigo-700">{p.className} - {p.subject}</div>
                    {p.notes && <div className="text-[10px] text-indigo-500 mt-0.5">{p.notes}</div>}
                  </div>
                  <button onClick={() => deletePlan(p.id)} className="text-red-400 hover:text-red-600 text-xs">X</button>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2 border-t border-school-border pt-3">
            <input
              type="text"
              value={form.className}
              onChange={(e) => setForm({ ...form, className: e.target.value })}
              placeholder="Class name (e.g. Play)"
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm"
            />
            <input
              type="text"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
              placeholder="Subject (e.g. Math)"
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm"
            />
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Notes (optional)"
              className="w-full px-3 py-2 border border-school-border rounded-xl text-sm"
            />
            <button
              onClick={addPlan}
              disabled={saving || !form.className.trim() || !form.subject.trim()}
              className="w-full py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold disabled:opacity-50"
            >
              {saving ? 'Adding...' : '+ Add Plan'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
