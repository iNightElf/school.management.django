interface AIResultTableProps {
  columns: string[];
  data: Record<string, string>[];
}

const AIResultTable = ({ columns, data }: AIResultTableProps) => {
  if (!data.length) return null;
  return (
    <div className="max-h-64 overflow-auto rounded-xl border border-school-border">
      <table className="w-full text-xs">
        <thead className="bg-school-primary text-school-paper sticky top-0">
          <tr>
            {columns.map((col) => (
              <th key={col} className="px-3 py-2 text-left font-semibold">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white/50' : 'bg-transparent'}>
              {columns.map((col) => (
                <td key={col} className="px-3 py-1.5 border-t border-school-border/50">{row[col] ?? '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AIResultTable;
