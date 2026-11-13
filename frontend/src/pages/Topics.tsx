import { useEffect, useState } from "react";
import { api, TopicItem } from "../api/client";
import { Card } from "../components/Card";

export default function Topics() {
  const [topics, setTopics] = useState<TopicItem[]>([]);
  useEffect(() => {
    api.topics().then(setTopics).catch(() => setTopics([]));
  }, []);

  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {topics.map((t) => (
        <Card key={t.id} title={t.label}>
          <div className="text-xs text-slate-500 mb-2">{t.size} documents</div>
          <ul className="mb-3 space-y-1 text-sm text-slate-700">
            {t.examples.map((e) => (
              <li key={e.id} className="line-clamp-2">
                {e.url ? (
                  <a href={e.url} target="_blank" rel="noreferrer" className="hover:underline">{e.title}</a>
                ) : (
                  e.title
                )}
              </li>
            ))}
          </ul>
          <div className="flex flex-wrap gap-1">
            {t.keywords.map((k) => (
              <span key={k} className="text-xs bg-brand-50 text-brand-700 rounded px-2 py-0.5">{k}</span>
            ))}
          </div>
        </Card>
      ))}
      {topics.length === 0 && (
        <div className="text-slate-500 text-sm">
          No topics yet. Run <code>python -m backend.scripts.run_pipeline</code>.
        </div>
      )}
    </div>
  );
}
