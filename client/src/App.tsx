import { useEffect, Suspense, lazy, useState } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store';
import ErrorBoundary from './components/ErrorBoundary';
import NotFound from './pages/NotFound';
import AICommandPalette from './ai/AICommandPalette';
import { usePullToRefresh } from './lib/usePullToRefresh';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const PinAttendance = lazy(() => import('./pages/PinAttendance'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const AuditLogs = lazy(() => import('./pages/AuditLogs'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ParentDashboard = lazy(() => import('./pages/parents/ParentDashboard'));
const ParentAttendance = lazy(() => import('./pages/parents/ParentAttendance'));
const ParentFees = lazy(() => import('./pages/parents/ParentFees'));
const ParentResults = lazy(() => import('./pages/parents/ParentResults'));
const ParentAnnouncements = lazy(() => import('./pages/parents/ParentAnnouncements'));

function PageLoader() {
  return (
    <div className="min-h-screen bg-school-paper flex items-center justify-center">
      <div className="w-8 h-8 border-3 border-school-primary/20 border-t-school-primary rounded-full animate-spin"></div>
    </div>
  );
}

const App: React.FC = () => {
  const { user, loading, fetchSession } = useAuthStore();
  const [installPrompt, setInstallPrompt] = useState<any>(null);
  usePullToRefresh();

  // Capture the install prompt event
  useEffect(() => {
    const handler = (e: Event) => { e.preventDefault(); setInstallPrompt(e); };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    const result = await installPrompt.userChoice;
    if (result.outcome === 'accepted') setInstallPrompt(null);
  };

  const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
  const isPWA = window.location.search.includes('pwa=true') || 
                window.location.search.includes('mode=pwa') || 
                isStandalone || 
                (navigator as any).standalone;

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  if (loading) {
    return <PageLoader />;
  }

  return (
    <Router>
      <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={!user ? <Login /> : <Navigate to={user.role === 'parent' ? '/parent' : '/'} />} />
          <Route path="/register" element={!user ? <Register /> : <Navigate to={user.role === 'parent' ? '/parent' : '/'} />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/users" element={user?.role === 'admin' ? <UserManagement /> : <Navigate to="/" />} />
          <Route path="/audit" element={user?.role === 'admin' ? <AuditLogs /> : <Navigate to="/" />} />
          <Route path="/pin-attendance" element={<PinAttendance />} />
          <Route path="/m" element={<Navigate to="/?mode=attendance" replace />} />

          <Route path="/" element={user ? (user.role === 'parent' ? <Navigate to="/parent" /> : <Dashboard />) : (isPWA ? <Navigate to="/pin-attendance" /> : <Navigate to="/login" />)} />
          <Route path="/parent" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentDashboard /> : <Navigate to="/" />} />
          <Route path="/parent/attendance" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentAttendance /> : <Navigate to="/" />} />
          <Route path="/parent/attendance/:studentId" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentAttendance /> : <Navigate to="/" />} />
          <Route path="/parent/fees" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentFees /> : <Navigate to="/" />} />
          <Route path="/parent/fees/:studentId" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentFees /> : <Navigate to="/" />} />
          <Route path="/parent/results" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentResults /> : <Navigate to="/" />} />
          <Route path="/parent/results/:studentId" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentResults /> : <Navigate to="/" />} />
          <Route path="/parent/announcements" element={user?.role === 'parent' || user?.role === 'admin' ? <ParentAnnouncements /> : <Navigate to="/" />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
      <AICommandPalette />
      </ErrorBoundary>

      {installPrompt && !isStandalone && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-school-primary text-white px-4 py-3 flex items-center justify-between shadow-lg">
          <p className="text-xs font-medium">Install <strong>AL RAWA</strong> for quick access</p>
          <div className="flex gap-2">
            <button onClick={() => setInstallPrompt(null)} className="px-3 py-1.5 text-xs text-white/70 hover:text-white">Not now</button>
            <button id="pwa-install-btn" onClick={handleInstall} className="px-4 py-1.5 bg-school-accent text-white rounded-lg text-xs font-bold hover:opacity-90">Install</button>
          </div>
        </div>
      )}
    </Router>
  );
};

export default App;
