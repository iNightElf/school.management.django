import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';

let client: SupabaseClient | null = null;
const ready: Promise<SupabaseClient> = (async () => {
  try {
    const res = await fetch('/api/config');
    if (res.ok) {
      const data = await res.json();
      if (data.supabaseUrl && data.supabaseAnonKey) {
        client = createClient(data.supabaseUrl, data.supabaseAnonKey);
        return client;
      }
    }
  } catch (e) {
    console.warn('[supabase] Failed to fetch config from /api/config:', e);
  }
  const url = import.meta.env.VITE_SUPABASE_URL || '';
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
  if (url && key) {
    client = createClient(url, key);
  } else {
    console.warn('Supabase URL or Anon Key not set. Photo uploads will not work.');
  }
  return client as SupabaseClient;
})();

export { ready };
export async function getClient() {
  return ready;
}
