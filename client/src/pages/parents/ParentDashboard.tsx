import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../store';
import { ChevronRight, GraduationCap, Megaphone } from 'lucide-react';
import ParentLayout from './ParentLayout';
import Toast, { toast } from '../../components/Toast';

interface Student {
  id: string;
  studentId: string;
  name: string;
  roll: string;
  klass: string;
  session: string;
  photoUrl: string | null;
}

interface Announcement {
  id: string;
  title: string;
  body: string;
  createdAt: string;
}

export default function ParentDashboard() {
  const navigate = useNavigate();
  const [students, setStudents] = useState<Student[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/parents/my-students/'),
      api.get('/parents/announcements/'),
    ])
      .then(([stuRes, annRes]) => {
        setStudents(stuRes.data);
        setAnnouncements(annRes.data.slice(0, 3));
      })
      .catch(() => toast('Failed to load data', 'error'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <ParentLayout>
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse bg-white rounded-xl p-5 border border-school-border">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      </ParentLayout>
    );
  }

  return (
    <ParentLayout>
      <Toast />
      <div className="space-y-4">
        <div className="bg-gradient-to-br from-school-primary to-school-secondary rounded-2xl p-5 text-white">
          <h2 className="font-serif text-xl">My Children</h2>
          <p className="text-sm text-white/70 mt-1">Select a student to view details</p>
        </div>

        {students.length === 0 && (
          <div className="bg-white rounded-xl border border-school-border p-8 text-center">
            <GraduationCap size={40} className="mx-auto text-school-muted mb-3" />
            <p className="text-school-muted font-medium">No students linked to your account</p>
            <p className="text-sm text-school-muted mt-1">Contact the school admin to link your children.</p>
          </div>
        )}

        {students.map((s) => (
          <div
            key={s.id}
            onClick={() => navigate(`/parent/attendance/${s.id}`)}
            className="bg-white rounded-xl border border-school-border p-4 card-shadow hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-school-accent to-school-accent2 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                {s.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-school-primary truncate">{s.name}</h3>
                <p className="text-xs text-school-muted mt-0.5">
                  {s.klass} · Roll: {s.roll} · ID: {s.studentId}
                </p>
              </div>
              <ChevronRight size={20} className="text-school-muted flex-shrink-0" />
            </div>
          </div>
        ))}

        {announcements.length > 0 && (
          <div className="bg-white rounded-xl border border-school-border overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-school-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Megaphone size={16} className="text-school-accent" />
                <span className="font-bold text-sm text-school-primary">Recent Updates</span>
              </div>
              <button
                onClick={() => navigate('/parent/announcements')}
                className="text-[11px] font-semibold text-school-accent hover:underline"
              >
                See all
              </button>
            </div>
            {announcements.map((a) => (
              <div key={a.id} className="px-4 py-3 border-b border-school-border last:border-0">
                <p className="font-semibold text-sm text-school-primary">{a.title}</p>
                {a.body && <p className="text-xs text-school-muted mt-0.5 line-clamp-2">{a.body}</p>}
                <p className="text-[10px] text-school-muted/60 mt-1">{new Date(a.createdAt).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </ParentLayout>
  );
}
