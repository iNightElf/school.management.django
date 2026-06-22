interface AIResultSummaryProps {
  explanation: string;
}

const AIResultSummary = ({ explanation }: AIResultSummaryProps) => (
  <p className="text-sm text-school-ink/70 dark:text-[#c0c0c8] leading-relaxed">{explanation}</p>
);

export default AIResultSummary;
