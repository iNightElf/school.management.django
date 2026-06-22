import { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Command, ArrowRight, X, Sparkles } from 'lucide-react';
import { useAIQueryStore } from '../store';
import AIResultPanel from './AIResultPanel';

const SUGGESTIONS = [
  'Show fee status of student ID 101',
  'Class 7 attendance summary',
  'Search student named Ahmed',
  'Defaulters in Class 8',
  'Teacher subjects for Ms. Fatima',
  'Dashboard summary',
  'Bank account balances',
  'List students in Class 5',
];

const AICommandPalette = () => {
  const { open, query, loading, result, error, setOpen, setQuery, submit, close } = useAIQueryStore();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(!open);
      }
      if (e.key === 'Escape' && open) {
        close();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, setOpen, close]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  const handleSubmit = useCallback(() => {
    const q = query.trim();
    if (!q || loading) return;
    submit(q);
  }, [query, loading, submit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
  }, [handleSubmit]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/40 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) close(); }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl mx-4 bg-school-paper dark:bg-[#1a1a2e] rounded-2xl shadow-2xl border border-school-border overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-school-border">
              <Search size={20} className="text-school-muted shrink-0" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about school data…"
                className="flex-1 bg-transparent text-sm text-school-ink dark:text-[#e0e0e8] placeholder-school-muted outline-none"
              />
              <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-md bg-school-border/50 text-[10px] text-school-muted font-mono">
                <Command size={12} /><span>K</span>
              </kbd>
              <button
                onClick={handleSubmit}
                disabled={!query.trim() || loading}
                className="p-1.5 rounded-lg bg-school-accent text-white disabled:opacity-40 hover:bg-school-accent/90 transition-colors"
                aria-label="Submit query"
              >
                <ArrowRight size={16} />
              </button>
              <button
                onClick={close}
                className="p-1.5 rounded-lg hover:bg-school-border/50 transition-colors text-school-muted"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Results or suggestions */}
            <div className="px-4 py-3 max-h-96 overflow-y-auto">
              {result || loading || error ? (
                <AIResultPanel loading={loading} result={result} error={error} />
              ) : (
                <div className="space-y-2">
                  <p className="text-[10px] uppercase tracking-widest text-school-muted font-semibold">
                    Try asking…
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        onClick={() => { setQuery(s); submit(s); }}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-school-border/40 hover:bg-school-border/70 text-[11px] text-school-ink/70 dark:text-[#c0c0c8] transition-colors"
                      >
                        <Sparkles size={12} />
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AICommandPalette;
