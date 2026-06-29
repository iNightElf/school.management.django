import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store';
import { SCHOOL_LOGO } from '../../lib/logo';
import { usePushSubscription } from '../../lib/usePushSubscription';
import { getInstallPrompt, isStandalone, swapManifest } from '../../lib/pwa';
import { Home, CalendarCheck, Wallet, BarChart3, Megaphone, LogOut, ArrowLeft, Download } from 'lucide-react';

const tabs = [
  { path: '/parent', label: 'Home', icon: Home },
  { path: '/parent/attendance', label: 'Attendance', icon: CalendarCheck },
  { path: '/parent/fees', label: 'Fees', icon: Wallet },
  { path: '/parent/results', label: 'Results', icon: BarChart3 },
  { path: '/parent/announcements', label: 'Updates', icon: Megaphone },
];

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const currentPath = window.location.hash.replace('#', '');
  usePushSubscription();

  useEffect(() => {
    swapManifest('parent-manifest.json');
  }, []);

  const standalone = isStandalone();
  const prompt = getInstallPrompt();
  const [showInstall, setShowInstall] = useState(false);
  const [installing, setInstalling] = useState(false);
  useEffect(() => { setShowInstall(!!prompt && !standalone); }, [prompt, standalone]);

  const handleInstall = async () => {
    const p = getInstallPrompt();
    if (!p) return;
    setInstalling(true);
    p.prompt();
    const result = await p.userChoice;
    if (result.outcome === 'accepted') setShowInstall(false);
    setInstalling(false);
  };

  const isActive = (path: string) =>
    path === '/parent' ? currentPath === '/parent' : currentPath.startsWith(path);

  return (
    <div className="min-h-screen bg-school-paper flex flex-col">
      <header className="sticky top-0 z-50 bg-school-primary text-school-paper shadow-lg px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={SCHOOL_LOGO} alt="Logo" className="w-9 h-9 rounded-full object-cover ring-2 ring-white/20 shadow-sm" />
          <div>
            <h1 className="font-serif text-lg leading-tight">AL RAWA</h1>
            <p className="text-[9px] uppercase tracking-widest opacity-70">Parent Portal</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium opacity-80 hidden sm:inline">{user?.name}</span>
          {user?.role === 'admin' && (
            <button onClick={() => navigate('/')} className="p-2 hover:bg-white/10 rounded-full transition-colors" title="Back to Dashboard">
              <ArrowLeft size={18} />
            </button>
          )}
          {showInstall && (
            <button onClick={handleInstall} disabled={installing} className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-bold bg-school-accent text-white rounded-lg hover:opacity-90 transition-opacity" title="Install Parent Portal">
              <Download size={14} /> {installing ? '...' : 'Install'}
            </button>
          )}
          <button onClick={logout} className="p-2 hover:bg-white/10 rounded-full transition-colors" title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <main className="flex-1 p-4 max-w-3xl mx-auto w-full">{children}</main>

      <nav className="sticky bottom-0 z-50 bg-white dark:bg-school-primary border-t border-school-border flex items-center justify-around py-1 safe-area-bottom">
        {tabs.map((t) => {
          const Icon = t.icon;
          const active = isActive(t.path);
          return (
            <button
              key={t.path}
              onClick={() => navigate(t.path)}
              className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors min-w-[56px] ${
                active ? 'text-school-accent' : 'text-school-muted hover:text-school-primary dark:hover:text-white'
              }`}
            >
              <Icon size={20} />
              <span className="text-[9px] font-semibold uppercase tracking-wider">{t.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
