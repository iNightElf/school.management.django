import { useNavigate } from 'react-router-dom';

interface AIResultTableProps {
  columns: string[];
  data: Record<string, string>[];
}

const NAV_COLUMNS = ['Student ID', 'Name', 'Student'];

export default function AIResultTable({ columns, data }: AIResultTableProps) {
  const navigate = useNavigate();

  const hasNav = columns.some((c) => NAV_COLUMNS.includes(c));
  const studentIdIdx = columns.indexOf('Student ID');

  const handleRowClick = (row: Record<string, string>) => {
    const sid = studentIdIdx >= 0 ? row[columns[studentIdIdx]] : '';
    if (sid) navigate(`/students/${sid}`);
  };

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
            <tr
              key={i}
              onClick={hasNav ? () => handleRowClick(row) : undefined}
              className={`${i % 2 === 0 ? 'bg-white/50' : 'bg-transparent'} ${hasNav ? 'cursor-pointer hover:bg-school-border/30' : ''}`}
            >
              {columns.map((col) => (
                <td key={col} className="px-3 py-1.5 border-t border-school-border/50">{row[col] ?? '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
