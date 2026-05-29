import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

export default function Sources() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api.sources().then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <Card title="Configured data sources">
      <table className="w-full text-sm">
        <thead className="text-left text-slate-500">
          <tr><th>ID</th><th>Name</th><th>Kind</th><th>Enabled</th></tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.id} className="border-t">
              <td className="py-1">{s.id}</td>
              <td>{s.name}</td>
              <td>{s.kind}</td>
              <td>{s.enabled ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
