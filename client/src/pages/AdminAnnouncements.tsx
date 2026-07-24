import { useEffect, useState } from 'react';
import { api } from '../store';
import Toast, { toast } from '../components/Toast';
import { Megaphone, Send, Loader2 } from 'lucide-react';

interface Announcement {
  id: string;
  title: string;
  body: string;
  author: string;
  school_class: { id: string; name: string } | null;
  createdAt: string;
}

interface SchoolClass {
  id: string;
  name: string;
}

export default function AdminAnnouncements() {
  const [items, setItems] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [classId, setClassId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetch = () => {
    setLoading(true);
    Promise.all([
      api.get('/parents/announcements/'),
      api.get('/classes/'),
    ])
      .then(([annRes, clsRes]) => {
        setItems(annRes.data);
        setClasses(clsRes.data ?? []);
      })
      .catch(() => toast('Failed to load announcements', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return toast('Title is required', 'error');
    setSubmitting(true);
    try {
      const payload: Record<string, any> = { title: title.trim(), body: body.trim() };
      if (classId) payload.school_class_id = classId;
      const res = await api.post('/parents/announcements/', payload);
      setItems((prev) => [res.data, ...prev]);
      setTitle('');
      setBody('');
      setClassId('');
      toast('Announcement sent!', 'success');
    } catch {
      toast('Failed to create announcement', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Toast />
      <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl p-5 text-white">
        <div className="flex items-center gap-3 mb-1">
          <Megaphone size={24} />
          <h2 className="font-serif text-xl">Announcements</h2>
        </div>
        <p className="text-sm text-white/70">Create and manage school announcements</p>
      </div>

      {/* Create Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-school-border p-5 space-y-4">
        <h3 className="font-bold text-school-primary flex items-center gap-2">
          <Send size={16} /> New Announcement
        </h3>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title *"
          className="w-full px-4 py-2.5 rounded-xl border border-school-border bg-school-bg text-sm focus:outline-none focus:ring-2 focus:ring-school-accent/30"
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Body (optional)"
          rows={3}
          className="w-full px-4 py-2.5 rounded-xl border border-school-border bg-school-bg text-sm focus:outline-none focus:ring-2 focus:ring-school-accent/30 resize-none"
        />
        <div className="flex items-center gap-3">
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-school-border bg-school-bg text-sm focus:outline-none focus:ring-2 focus:ring-school-accent/30"
          >
            <option value="">All classes</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={submitting || !title.trim()}
            className="ml-auto px-5 py-2.5 rounded-xl bg-school-accent text-white text-sm font-semibold hover:bg-school-accent/90 disabled:opacity-50 flex items-center gap-2"
          >
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            Send
          </button>
        </div>
      </form>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-white rounded-xl p-4 border border-school-border">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-full" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center border border-school-border">
          <Megaphone size={40} className="mx-auto text-school-muted mb-3" />
          <p className="text-school-muted font-medium">No announcements yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-school-border p-4 space-y-2">
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-bold text-school-primary">{a.title}</h3>
                <span className="text-[10px] text-school-muted whitespace-nowrap shrink-0">
                  {new Date(a.createdAt).toLocaleDateString()}
                </span>
              </div>
              {a.body && <p className="text-sm text-school-muted leading-relaxed">{a.body}</p>}
              <div className="flex items-center gap-3 text-[10px] text-school-muted/60">
                <span>— {a.author}</span>
                {a.school_class && (
                  <span className="px-2 py-0.5 rounded-full bg-purple-50 text-purple-600 font-medium">
                    {a.school_class.name}
                  </span>
                )}
                {!a.school_class && (
                  <span className="px-2 py-0.5 rounded-full bg-green-50 text-green-600 font-medium">
                    All classes
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
