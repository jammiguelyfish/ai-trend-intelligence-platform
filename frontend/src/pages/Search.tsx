import { useState } from "react";
import { useEffect } from "react";
import { api, DEMO, exampleQueries, SearchResult } from "../api/client";
import { Card } from "../components/Card";

export default function Search() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Record<number, string>>({});
  const [examples, setExamples] = useState<string[]>([]);

  useEffect(() => {
    if (DEMO) exampleQueries().then(setExamples).catch(() => setExamples([]));
  }, []);

  async function run(query: string) {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const r = await api.search(query, 10);
      setResults(r.results);
    } finally {
      setLoading(false);
    }
  }

  function go(e: React.FormEvent) {
    e.preventDefault();
    run(q);
  }

  async function summarize(id: number) {
    const s = await api.summarize(id);
    setSummary((prev) => ({ ...prev, [id]: s.content }));
  }

  return (
    <div className="space-y-4">
      <form onSubmit={go} className="flex gap-2">
        <input
          className="flex-1 border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Search developer/AI trends semantically…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          className="bg-brand-500 text-white px-4 py-2 rounded-md hover:bg-brand-700"
          disabled={loading}
        >
          {loading ? "…" : "Search"}
        </button>
      </form>

      {DEMO && (
        <div className="text-xs text-slate-600 space-y-2">
          <p>
            Try an example (real semantic search results, precomputed). Other
            queries use plain keyword matching in your browser, because the
            embedding model only runs in the full app.
          </p>
          <div className="flex flex-wrap gap-2">
            {examples.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => { setQ(ex); run(ex); }}
                className="border rounded-full px-3 py-1 hover:bg-brand-50"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {results.map((r) => (
          <Card key={r.id}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <a href={r.url ?? "#"} target="_blank" rel="noreferrer" className="text-brand-700 font-medium hover:underline">
                  {r.title}
                </a>
                <p className="text-sm text-slate-600 mt-1">{r.snippet}</p>
                <div className="text-xs text-slate-500 mt-2">
                  {r.published_at ?? ""} • score {r.score?.toFixed(3)}
                </div>
                {summary[r.id] && (
                  <pre className="bg-slate-50 border rounded p-3 text-xs whitespace-pre-wrap mt-3">{summary[r.id]}</pre>
                )}
              </div>
              {!DEMO && (
                <button
                  onClick={() => summarize(r.id)}
                  className="text-xs border rounded px-2 py-1 hover:bg-brand-50"
                >
                  Summarize
                </button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
