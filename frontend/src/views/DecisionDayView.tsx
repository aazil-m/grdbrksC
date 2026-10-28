import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { api } from '../api/client';
import type { DayResponse } from '../api/types';
import { useApi } from '../api/useApi';
import { COLORS, Loadable, Panel, StatCard } from '../components/ui';
import { hours, mw, signedMw, ukDateTime, ukTime } from '../format';

interface Row {
  t: number;
  actual?: number;
  forecast?: number;
}

function toRows(day: DayResponse): Row[] {
  const rows = new Map<number, Row>();
  for (const a of day.actuals) {
    const t = Date.parse(a.start);
    rows.set(t, { ...rows.get(t), t, actual: a.generation });
  }
  for (const p of day.points) {
    const t = Date.parse(p.start);
    rows.set(t, { ...rows.get(t), t, forecast: p.forecast ?? undefined });
  }
  return [...rows.values()].sort((a, b) => a.t - b.t);
}

function runsUsed(day: DayResponse): string {
  const runs = [...new Set(day.points.flatMap((p) => (p.publishTime ? [p.publishTime] : [])))];
  if (runs.length === 0) return 'None';
  const horizons = day.points.flatMap((p) => (p.horizonHours === null ? [] : [p.horizonHours]));
  const range = `${hours(Math.min(...horizons))}–${hours(Math.max(...horizons))} ahead`;
  return `${runs.map(ukDateTime).join(', ')} (${range})`;
}

export function DecisionDayView({ date, cutoff }: { date: string; cutoff: string }) {
  const state = useApi(`day:${date}:${cutoff}`, (signal) => api.day(date, cutoff, signal));
  return (
    <Loadable state={state}>
      {(day) => (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard
              label="MAE"
              value={day.summary ? mw(day.summary.mae) : '—'}
              hint="Mean absolute error over the day's hourly points"
            />
            <StatCard
              label="Bias"
              value={day.summary ? signedMw(day.summary.bias) : '—'}
              hint="Mean of forecast − actual. Positive: forecast too high"
            />
            <StatCard
              label="Largest miss"
              value={day.summary ? mw(day.summary.maxAbsError) : '—'}
            />
            <StatCard
              label="Missing hours"
              value={`${day.missingHours} / ${day.points.length}`}
              hint="Hours with no forecast published before the cutoff"
            />
          </div>
          <Panel
            title="Forecast available at decision time vs actual generation"
            subtitle={`Forecast run used: ${runsUsed(day)}. Cutoff ${ukDateTime(day.cutoffUtc)} UK.`}
          >
            <div className="h-80">
              <ResponsiveContainer>
                <LineChart data={toRows(day)} margin={{ left: 16, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="t"
                    type="number"
                    scale="time"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={ukTime}
                  />
                  <YAxis tickFormatter={(v: number) => `${v / 1000} GW`} />
                  <Tooltip
                    labelFormatter={(t) => ukDateTime(Number(t))}
                    formatter={(v) => mw(Number(v))}
                  />
                  <Legend />
                  <Line
                    name="Actual (half-hourly)"
                    dataKey="actual"
                    stroke={COLORS.actual}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />
                  <Line
                    name="Decision-time forecast (hourly)"
                    dataKey="forecast"
                    stroke={COLORS.forecast}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>
      )}
    </Loadable>
  );
}
