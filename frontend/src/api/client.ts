const BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export interface SearchResult {
  id: number;
  title: string;
  url?: string;
  score?: number;
  snippet?: string;
  published_at?: string;
}

export interface TrendItem {
  bucket: string;
  term: string;
  count: number;
  delta: number;
}

export interface TopicItem {
  id: number;
  label: string;
  keywords: string[];
  size: number;
}

export const api = {
  health: () => jget<{ status: string; vectors: number }>("/health"),
  sources: () => jget<any[]>("/sources"),
  search: (q: string, k = 10) =>
    jget<{ query: string; count: number; results: SearchResult[] }>(
      `/search?q=${encodeURIComponent(q)}&k=${k}`
    ),
  trends: (bucket?: string, limit = 50) =>
    jget<{ bucket: string | null; items: TrendItem[] }>(
      `/trends?${bucket ? `bucket=${bucket}&` : ""}limit=${limit}`
    ),
  buckets: () => jget<{ buckets: string[] }>("/trends/buckets"),
  topics: () => jget<TopicItem[]>("/topics"),
  summarize: (document_id: number) =>
    jpost<{ id: number; content: string }>("/summary", { document_id }),
};
