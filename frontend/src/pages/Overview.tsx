import { useEffect, useState } from "react";
import { api, TrendItem } from "../api/client";
import { Card } from "../components/Card";
import { TrendChart } from "../components/TrendChart";

export default function Overview() {
  const [health, setHealth] = useState<{ status: string; vectors: number } | null>(null);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [topicCount, setTopicCount] = useState<number>(0);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.trends(undefined, 15).then((r) => setTrends(r.items)).catch(() => {});
    api.topics().then((t) => setTopicCount(t.length)).catch(() => {});
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card title="Status">
        <div className="text-2xl font-semibold text-brand-700">{health?.status ?? "…"}</div>
        <div className="text-xs text-slate-500 mt-1">Vectors: {health?.vectors ?? "?"}</div>
      </Card>
      <Card title="Active Topics">
        <div className="text-2xl font-semibold">{topicCount}</div>
      </Card>
      <Card title="Top Terms Today">
        <div className="text-2xl font-semibold">{trends.length}</div>
      </Card>
      <div className="md:col-span-3">
        <Card title="Trending terms">
          <TrendChart items={trends} />
        </Card>
      </div>
    </div>
  );
}
