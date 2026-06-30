import { useState, useEffect } from 'react';

const LS_KEY = 'ios-prompt-dismissed';

export default function IOSInstallPrompt() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const dismissed = localStorage.getItem(LS_KEY);
    if (isIOS && !isStandalone && !dismissed) setVisible(true);
  }, []);

  const dismiss = () => {
    localStorage.setItem(LS_KEY, '1');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-school-primary text-white px-4 py-3 shadow-lg">
      <p className="text-xs font-medium mb-1">
        Install <strong>AL RAWA</strong> for quick access
      </p>
      <ol className="text-xs text-white/80 list-decimal list-inside space-y-0.5 mb-2">
        <li>Tap <strong>Share</strong> <span className="text-sm">⎙</span></li>
        <li>Scroll down & tap <strong>Add to Home Screen</strong></li>
      </ol>
      <button onClick={dismiss} className="text-xs text-school-accent font-bold hover:opacity-80">
        Got it
      </button>
    </div>
  );
}
