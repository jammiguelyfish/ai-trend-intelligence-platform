import { useEffect, useState } from "react";
import { api, TrendItem } from "../api/client";
import { Card } from "../components/Card";
import { TrendChart } from "../components/TrendChart";

export default function Trends() {
  const [buckets, setBuckets] = useState<string[]>([]);
  const [bucket, setBucket] = useState<string | undefined>();
  const [items, setItems] = useState<TrendItem[]>([]);

  useEffect(() => {
    api.buckets().then((r) => {
      setBuckets(r.buckets);
      setBucket(r.buckets[0]);
    });
  }, []);

  useEffect(() => {
    if (!bucket) return;
    api.trends(bucket, 50).then((r) => setItems(r.items));
  }, [bucket]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-600">Day:</span>
        <select
          className="border rounded px-2 py-1 text-sm"
          value={bucket ?? ""}
          onChange={(e) => setBucket(e.target.value)}
        >
          {buckets.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>
      <Card title={`Top terms — ${bucket ?? ""}`}>
        <TrendChart items={items} />
      </Card>
      <Card title="All terms">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr><th>Term</th><th>Count</th><th>Δ vs prev</th></tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.term} className="border-t">
                <td className="py-1">{t.term}</td>
                <td>{t.count}</td>
                <td className={t.delta > 0 ? "text-green-600" : "text-slate-500"}>{t.delta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
