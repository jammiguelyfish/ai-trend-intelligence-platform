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
  examples: { id: number; title: string; url: string | null }[];
}

const liveApi = {
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

// ---- Static demo mode (GitHub Pages): no backend, read a JSON snapshot ----
export const DEMO = (import.meta as any).env?.VITE_DEMO === "1";
const DEMO_BASE = `${(import.meta as any).env?.BASE_URL ?? "/"}demo/`;

async function sget<T>(file: string): Promise<T> {
  const r = await fetch(`${DEMO_BASE}${file}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

interface DemoDoc {
  id: number;
  title: string;
  url: string | null;
  snippet: string;
  published_at: string | null;
}

interface SearchExamples {
  queries: string[];
  results: Record<string, SearchResult[]>;
}

let docsCache: Promise<DemoDoc[]> | null = null;
let examplesCache: Promise<SearchExamples> | null = null;

const loadDocs = () => (docsCache ??= sget<DemoDoc[]>("documents.json"));
const loadExamples = () => (examplesCache ??= sget<SearchExamples>("search_examples.json"));

export const exampleQueries = async () => (await loadExamples()).queries;

// The live app embeds the query with a local model. The hosted demo can't, so
// example queries return the real precomputed semantic results and anything
// else falls back to simple keyword matching.
async function demoSearch(q: string, k = 10) {
  const ex = await loadExamples();
  const hit = ex.queries.find((e) => e.toLowerCase() === q.trim().toLowerCase());
  if (hit) {
    const results = ex.results[hit].slice(0, k);
    return { query: q, count: results.length, results };
  }
  const words = q.toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2);
  const docs = await loadDocs();
  const scored = docs
    .map((d) => {
      const title = d.title.toLowerCase();
      const body = d.snippet.toLowerCase();
      let score = 0;
      for (const w of words) {
        if (title.includes(w)) score += 3;
        if (body.includes(w)) score += 1;
      }
      return { d, score };
    })
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
  const top = scored.length ? scored[0].score : 1;
  const results = scored.map(({ d, score }) => ({
    id: d.id,
    title: d.title,
    url: d.url ?? undefined,
    snippet: d.snippet,
    published_at: d.published_at ?? undefined,
    score: score / top,
  }));
  return { query: q, count: results.length, results };
}

const demoApi: typeof liveApi = {
  health: () => sget("health.json"),
  sources: () => sget("sources.json"),
  search: demoSearch,
  trends: async (bucket, limit = 50) => {
    const r = await sget<{ bucket: string | null; items: TrendItem[] }>(
      `trends/${bucket ?? "latest"}.json`
    );
    return { ...r, items: r.items.slice(0, limit) };
  },
  buckets: () => sget("buckets.json"),
  topics: () => sget("topics.json"),
  summarize: async () => {
    throw new Error("Summaries need a local LLM and are not available in the hosted demo");
  },
};

export const api = DEMO ? demoApi : liveApi;
