import { motion } from 'framer-motion';
import { AlertCircle, Loader2, Sparkles } from 'lucide-react';
import AIResultTable from './AIResultTable';
import AIResultSummary from './AIResultSummary';

interface AIQueryResult {
  type: 'table' | 'summary' | 'clarification' | 'error';
  explanation: string;
  data: Record<string, string>[];
  columns: string[];
  confidence: number;
  meta: Record<string, unknown>;
}

interface AIResultPanelProps {
  loading: boolean;
  result: AIQueryResult | null;
  error: string | null;
}

const AIResultPanel = ({ loading, result, error }: AIResultPanelProps) => {
  if (loading) {
    return (
      <div className="flex items-center gap-3 py-6 text-school-muted">
        <Loader2 size={18} className="animate-spin" />
        <span className="text-sm">Querying school data…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-start gap-3 py-4 text-red-600 dark:text-red-400">
        <AlertCircle size={18} className="shrink-0 mt-0.5" />
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      <div className="flex items-start gap-2">
        <Sparkles size={16} className="text-school-accent shrink-0 mt-0.5" />
        <p className="text-sm font-medium text-school-ink dark:text-[#e0e0e8]">
          {result.explanation}
        </p>
      </div>

      {result.confidence < 1 && result.type !== 'error' && (
        <p className="text-[11px] text-school-muted">
          Confidence: {(result.confidence * 100).toFixed(0)}%
        </p>
      )}

      {result.type === 'table' && (
        <AIResultTable columns={result.columns} data={result.data} />
      )}

      {(result.type === 'summary' || result.type === 'clarification') && (
        <AIResultSummary explanation={result.explanation} />
      )}

      {result.type === 'error' && (
        <div className="flex items-start gap-3 py-2 text-red-600 dark:text-red-400">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <p className="text-sm">{result.explanation}</p>
        </div>
      )}

      {result.meta?.execution_time_ms != null && (
        <p className="text-[10px] text-school-muted/60 text-right">
          {(result.meta.execution_time_ms as number) < 1000
            ? `${result.meta.execution_time_ms}ms`
            : `${((result.meta.execution_time_ms as number) / 1000).toFixed(1)}s`}
        </p>
      )}
    </motion.div>
  );
};

export default AIResultPanel;
