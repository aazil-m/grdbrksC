import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { api } from '../api/client';
import type { VintagesResponse } from '../api/types';
import { useApi } from '../api/useApi';
import { COLORS, Loadable, Panel } from '../components/ui';
import { mw, ukDateTime, ukTime } from '../format';

type Row = Record<string, number>;

function toRows(data: VintagesResponse): Row[] {
  const rows = new Map<number, Row>();
  const set = (iso: string, key: string, value: number) => {
    const t = Date.parse(iso);
    const row: Row = rows.get(t) ?? { t };
    row[key] = value;
    rows.set(t, row);
  };
  data.actuals.forEach((a) => set(a.start, 'actual', a.generation));
  data.runs.forEach((run, i) => run.points.forEach((p) => set(p.start, `run${i}`, p.generation)));
  return [...rows.values()].sort((a, b) => a.t - b.t);
}

export function VintagesView({ date, cutoff }: { date: string; cutoff: string }) {
  const state = useApi(`vintages:${date}:${cutoff}`, (signal) =>
    api.vintages(date, cutoff, signal),
  );
  return (
    <Loadable state={state}>
      {(data) => {
        const runNames = new Map(data.runs.map((run, i) => [`run${i}`, run]));
        return (
          <Panel
            title="How the forecast for this day evolved"
            subtitle={`${data.runs.length} forecast runs published before the day ended. Bold blue: the run available at your cutoff. Grey: other runs. Black: actual.`}
          >
            <div className="h-96">
              <ResponsiveContainer>
                <LineChart data={toRows(data)} margin={{ left: 16, right: 16 }}>
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
                    formatter={(v, key) => {
                      const run = runNames.get(String(key));
                      return [mw(Number(v)), run ? `Run ${ukDateTime(run.publishTime)}` : 'Actual'];
                    }}
                  />
                  {data.runs.map((run, i) =>
                    run.isDecisionRun ? null : (
                      <Line
                        key={run.publishTime}
                        dataKey={`run${i}`}
                        stroke={COLORS.otherRun}
                        dot={false}
                        strokeWidth={1}
                        connectNulls
                        isAnimationActive={false}
                      />
                    ),
                  )}
                  {data.runs.map((run, i) =>
                    run.isDecisionRun ? (
                      <Line
                        key={run.publishTime}
                        dataKey={`run${i}`}
                        stroke={COLORS.forecast}
                        dot={false}
                        strokeWidth={3}
                        connectNulls
                        isAnimationActive={false}
                      />
                    ) : null,
                  )}
                  <Line
                    dataKey="actual"
                    stroke={COLORS.actual}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        );
      }}
    </Loadable>
  );
}
