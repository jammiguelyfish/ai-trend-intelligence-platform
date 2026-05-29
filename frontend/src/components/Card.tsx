import { PropsWithChildren } from "react";

export function Card({ title, children }: PropsWithChildren<{ title?: string }>) {
  return (
    <div className="bg-white border rounded-xl shadow-sm p-4">
      {title && <h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>}
      {children}
    </div>
  );
}
