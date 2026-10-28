import type { ReactNode } from 'react';

import type { ApiState } from '../api/useApi';

export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm" title={hint}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums text-slate-900">{value}</div>
    </div>
  );
}

export function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      <div className="mt-3">{children}</div>
    </section>
  );
}

export function Loadable<T>({
  state,
  children,
}: {
  state: ApiState<T>;
  children: (data: T) => ReactNode;
}) {
  if (state.status === 'loading') {
    return <p className="py-12 text-center text-sm text-slate-500">Loading…</p>;
  }
  if (state.status === 'error') {
    return (
      <p className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Could not load data: {state.message}
      </p>
    );
  }
  return <>{children(state.data)}</>;
}

export const COLORS = {
  actual: '#0f172a',
  forecast: '#2563eb',
  otherRun: '#cbd5e1',
  over: '#dc2626',
  under: '#16a34a',
  neutral: '#64748b',
};
