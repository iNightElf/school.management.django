import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useUIStore, useSchoolStore, useAuthStore } from '../store';
import { api } from '../store';
import Layout from '../components/Layout';
import Toast, { toast } from '../components/Toast';
import IdCardSection from './IdCardSection';
import AccessoriesSection from './AccessoriesSection';
import ResultSection from './ResultSection';
import FinanceSection from './FinanceSection';
import CoordinationSection from './coordination/CoordinationSection';
import EngagementWidget, { QuizPanel, RiddlePanel, MoodPanel, ChallengePanel, TipsPanel, PlannerPanel } from './engagement/EngagementWidget';
import { CreditCard, BookOpen, BarChart3, Wallet, Users, GraduationCap, Building2, Sparkles, ArrowRight, Clock, MailCheck, ClipboardList } from 'lucide-react';
import { SCHOOL_LOGO } from '../lib/logo';

type ModeParam = 'idcard' | 'accessories' | 'result' | 'finance' | 'coordination';

function TodaysGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good Morning';
  if (h < 17) return 'Good Afternoon';
  return 'Good Evening';
}

const Dashboard = () => {
  const { activeMode, setMode } = useUIStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const { studentTotal, teacherTotal, staffTotal, fetchClasses, fetchDashboardCounts } = useSchoolStore();
  const user = useAuthStore((s) => s.user);
  const isTeacher = user?.role === 'teacher';
  const isAdmin = user?.role === 'admin';
  const isPendingViewer = user?.role === 'viewer';
  const [verifying, setVerifying] = useState(false);
  const [verifySent, setVerifySent] = useState(false);
  const [engagementPanel, setEngagementPanel] = useState<string | null>(null);

  const handleResendVerification = async () => {
    setVerifying(true);
    try {
      await api.post('/auth/send-verification/');
      setVerifySent(true);
      toast('Verification email sent.', 'success');
    } catch (e) {
      toast('Failed to send verification email. Please try again.', 'error');
      if (import.meta.env.DEV) console.warn('[Dashboard] verification resend failed', e);
    }
    setVerifying(false);
  };

  useEffect(() => { document.title = 'Dashboard - AL RAWA English School'; }, []);
  useEffect(() => {
    fetchDashboardCounts();
    fetchClasses();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSetMode = (mode: ModeParam | null) => {
    setMode(mode);
    if (mode) setSearchParams({ mode }, { replace: false });
    else setSearchParams({}, { replace: false });
  };

  useEffect(() => {
    const urlMode = searchParams.get('mode') as ModeParam | null;
    if (urlMode && urlMode !== activeMode) {
      if (isPendingViewer || (urlMode === 'finance' && isTeacher)) {
        handleSetMode(null);
        return;
      }
      setMode(urlMode);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const MODULES = [
    { key: 'idcard' as ModeParam, label: 'ID Card', desc: 'Students, Teachers & Staff', color: 'blue', icon: CreditCard },
    { key: 'accessories' as ModeParam, label: 'Fees & Books', desc: 'Fee structure & book list', color: 'amber', icon: BookOpen },
    { key: 'result' as ModeParam, label: 'Result', desc: 'Marks & report cards', color: 'green', icon: BarChart3 },
    ...(!isTeacher && !isPendingViewer ? [{ key: 'finance' as ModeParam, label: 'Finance', desc: 'Accounting & fees', color: 'rose', icon: Wallet }] : []),
    ...((isAdmin || isTeacher) ? [{ key: 'coordination' as ModeParam, label: 'Coordination', desc: 'Alerts, interventions & tracking', color: 'purple', icon: ClipboardList }] : []),
  ];

  return (
    <Layout>
      <Toast />

      {!activeMode ? (
        <div className="space-y-5 animate-fade-in">
          {/* Welcome Banner */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-school-primary via-school-secondary to-school-accent2 p-6 text-white">
            <div className="absolute inset-0 bg-white/5 [mask-image:radial-gradient(ellipse_at_top_right,black_30%,transparent_70%)]" />
            <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
            <div className="relative flex items-center gap-4">
              <button onClick={() => handleSetMode(null)} className="hidden sm:block">
                <img src={SCHOOL_LOGO} alt="School logo" className="w-14 h-14 rounded-full border-2 border-white/20 shadow-lg object-cover cursor-pointer hover:scale-105 transition-transform" />
              </button>
              <div className="flex-1">
                <p className="text-sm text-white/70 font-medium">{TodaysGreeting()}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}</p>
                <h1 className="font-serif text-xl sm:text-2xl mt-0.5">AL RAWA English School</h1>
              </div>
              <div className="hidden sm:flex items-center gap-1 text-[10px] text-white/50 uppercase tracking-wider bg-white/10 px-3 py-1.5 rounded-full">
                <Sparkles size={12} />
                <span>{new Date().getFullYear()} Session</span>
              </div>
            </div>
          </div>

          {/* Email verification notice */}
          {user && !user.emailVerified && !isPendingViewer && (
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <MailCheck size={20} className="text-blue-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-blue-800">Verify your email address</p>
                <p className="text-xs text-blue-600">Check your inbox or resend the verification link.</p>
              </div>
              {verifySent ? (
                <span className="text-xs text-green-600 font-semibold">Sent!</span>
              ) : (
                <button onClick={handleResendVerification} disabled={verifying}
                  className="px-3 py-1.5 bg-blue-500 text-white text-xs font-semibold rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors">
                  {verifying ? 'Sending...' : 'Resend'}
                </button>
              )}
            </div>
          )}

          {/* Pending viewer notice */}
          {isPendingViewer && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center">
              <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock size={32} className="text-amber-500" />
              </div>
              <h3 className="font-serif text-lg font-bold text-amber-800 mb-2">Account Pending</h3>
              <p className="text-sm text-amber-700 max-w-sm mx-auto">
                Your account is awaiting role assignment. Please contact an admin to get access to the system.
              </p>
            </div>
          )}

          {/* Quick Stats */}
          {!isPendingViewer && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: GraduationCap, value: studentTotal, label: 'Students', color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-500/10' },
              { icon: Users, value: teacherTotal, label: 'Teachers', color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-500/10' },
              { icon: Building2, value: staffTotal, label: 'Staff', color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-500/10' },
            ].map((s) => (
              <div key={s.label} className="bg-white dark:bg-[#1a1a2e] rounded-xl border border-school-border dark:border-[#2a2a3e] p-4 card-shadow">
                <div className={`w-9 h-9 ${s.bg} rounded-xl flex items-center justify-center mb-2`}>
                  <s.icon size={18} className={s.color} />
                </div>
                <div className="font-bold text-lg text-school-primary dark:text-[#e0e0e8]">{s.value}</div>
                <div className="text-[10px] text-school-muted uppercase tracking-wider font-bold">{s.label}</div>
              </div>
            ))}
          </div>
          )}

          {/* Module Tiles */}
          {!isPendingViewer && (
          <div className="grid grid-cols-2 gap-3">
            {MODULES.map((m) => {
              const Icon = m.icon;
              const bgMap: Record<string, string> = { blue: 'from-blue-500 to-blue-700', amber: 'from-amber-500 to-orange-700', green: 'from-green-500 to-emerald-700', rose: 'from-rose-500 to-rose-700', purple: 'from-purple-500 to-purple-700' };
              return (
                <button key={m.key} onClick={() => handleSetMode(m.key)}
                  className="group relative bg-white dark:bg-[#1a1a2e] p-5 rounded-2xl border border-school-border dark:border-[#2a2a3e] text-left card-shadow overflow-hidden"
                >
                  <div className={`w-12 h-12 bg-gradient-to-br ${bgMap[m.color]} text-white rounded-2xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform shadow-sm`}>
                    <Icon size={24} />
                  </div>
                  <div className="font-bold text-sm text-school-primary dark:text-[#e0e0e8]">{m.label}</div>
                  <div className="text-[11px] text-school-muted mt-0.5">{m.desc}</div>
                  <ArrowRight size={14} className="absolute bottom-4 right-4 text-school-muted opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0" />
                </button>
              );
            })}
          </div>
          )}

          {/* Engagement Widget — teachers & admins */}
          {(isTeacher || isAdmin) && !isPendingViewer && (
            <EngagementWidget onOpenPanel={(p) => setEngagementPanel(p)} />
          )}
        </div>
      ) : (
        <div className="animate-fade-in">
          {activeMode === 'idcard' && <IdCardSection />}
          {activeMode === 'accessories' && <AccessoriesSection />}
          {activeMode === 'result' && <ResultSection />}
          {activeMode === 'finance' && <FinanceSection />}
          {activeMode === 'coordination' && <CoordinationSection />}
        </div>
      )}

      {/* Engagement Panels */}
      {engagementPanel === 'quiz' && <QuizPanel onClose={() => setEngagementPanel(null)} />}
      {engagementPanel === 'riddle' && <RiddlePanel onClose={() => setEngagementPanel(null)} />}
      {engagementPanel === 'mood' && <MoodPanel onClose={() => setEngagementPanel(null)} />}
      {engagementPanel === 'challenge' && <ChallengePanel onClose={() => setEngagementPanel(null)} />}
      {engagementPanel === 'tips' && <TipsPanel onClose={() => setEngagementPanel(null)} />}
      {engagementPanel === 'planner' && <PlannerPanel onClose={() => setEngagementPanel(null)} />}
    </Layout>
  );
};

export default Dashboard;
