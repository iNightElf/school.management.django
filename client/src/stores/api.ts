import axios from 'axios';
import { API_URL } from '../lib/config';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

const inflight = new Map<string, Promise<unknown>>();
export function dedupedFetch<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const existing = inflight.get(key);
  if (existing) return existing as Promise<T>;
  const p = fn().finally(() => inflight.delete(key));
  inflight.set(key, p);
  return p;
}
