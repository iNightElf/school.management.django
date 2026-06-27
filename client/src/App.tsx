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

  // Check if already installed
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches;

  useEffect(() => {
    const isPWA = window.location.search.includes('pwa=true') || 
                  window.location.search.includes('mode=pwa') || 
                  window.matchMedia('(display-mode: standalone)').matches || 
                  (navigator as any).standalone;
    const currentHash = window.location.hash;
    if (isPWA && (currentHash === '' || currentHash === '#/' || currentHash === '#/login')) {
      window.location.hash = '#/pin-attendance';
    }
  }, []);

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
          <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
          <Route path="/register" element={!user ? <Register /> : <Navigate to="/" />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/users" element={user?.role === 'admin' ? <UserManagement /> : <Navigate to="/" />} />
          <Route path="/audit" element={user?.role === 'admin' ? <AuditLogs /> : <Navigate to="/" />} />
          <Route path="/pin-attendance" element={<PinAttendance />} />
          <Route path="/m" element={<Navigate to="/?mode=attendance" replace />} />
          <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
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
