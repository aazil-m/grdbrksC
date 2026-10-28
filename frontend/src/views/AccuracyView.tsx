import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { api } from '../api/client';
import type { MetricsResponse } from '../api/types';
import { useApi } from '../api/useApi';
import { COLORS, Loadable, Panel, StatCard } from '../components/ui';
import { hours, mw, signedMw } from '../format';

const gw = (v: number) => `${(v / 1000).toFixed(1)} GW`;

function SummaryCards({ data }: { data: MetricsResponse }) {
  const s = data.summary;
  const cards: [string, string, string][] = s
    ? [
        ['MAE', mw(s.mae), 'Mean absolute error'],
        ['RMSE', mw(s.rmse), 'Root mean squared error: penalises large misses'],
        ['Bias', signedMw(s.bias), 'Mean of forecast − actual. Positive: forecast too high'],
        [
          'nMAE',
          s.nmaePct === null ? '—' : `${s.nmaePct.toFixed(1)} %`,
          'MAE as % of mean actual generation',
        ],
        ['P10 error', signedMw(s.p10), '10% of hours had an error below this'],
        ['P50 error', signedMw(s.p50), 'Median error'],
        ['P90 error', signedMw(s.p90), '90% of hours had an error below this'],
      ]
    : [];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-8">
      {cards.map(([label, value, hint]) => (
        <StatCard key={label} label={label} value={value} hint={hint} />
      ))}
      <StatCard
        label="Missing hours"
        value={`${data.missingHours} / ${data.totalHours}`}
        hint="Hours with no forecast published before the cutoff; excluded from all metrics"
      />
    </div>
  );
}

export function AccuracyView({
  cutoff,
  onSelectDay,
}: {
  cutoff: string;
  onSelectDay: (date: string) => void;
}) {
  const state = useApi(`metrics:${cutoff}`, (signal) => api.metrics(cutoff, signal));
  return (
    <Loadable state={state}>
      {(data) => {
        const inDecisionRange = (lower: number, upper: number) =>
          data.decisionHorizonMin !== null &&
          data.decisionHorizonMax !== null &&
          upper > data.decisionHorizonMin &&
          lower <= data.decisionHorizonMax;
        return (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-slate-600">
              Accuracy of the forecast available at <strong>{cutoff}</strong> on the day before
              delivery, over all delivery days. Error = forecast − actual, at hourly points.
            </p>
            <SummaryCards data={data} />
            <div className="grid gap-4 lg:grid-cols-2">
              <Panel
                title="Error distribution"
                subtitle="Hours by error size (500 MW bins). Right of zero: forecast too high."
              >
                <div className="h-64">
                  <ResponsiveContainer>
                    <BarChart
                      data={data.histogram.map((b) => ({ ...b, mid: (b.lower + b.upper) / 2 }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="mid" tickFormatter={gw} />
                      <YAxis allowDecimals={false} />
                      <Tooltip
                        labelFormatter={(_, payload) => {
                          const bin = payload?.[0]?.payload as
                            { lower: number; upper: number } | undefined;
                          return bin ? `${signedMw(bin.lower)} to ${signedMw(bin.upper)}` : '';
                        }}
                        formatter={(v) => [`${String(v)} hours`, 'Count']}
                      />
                      <Bar dataKey="count">
                        {data.histogram.map((b) => (
                          <Cell key={b.lower} fill={b.lower >= 0 ? COLORS.over : COLORS.under} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>
              <Panel title="Error by hour of day" subtitle="UK local hour of the delivery period.">
                <div className="h-64">
                  <ResponsiveContainer>
                    <BarChart data={data.byHourOfDay}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="key" />
                      <YAxis tickFormatter={gw} />
                      <Tooltip
                        formatter={(v) => mw(Number(v))}
                        labelFormatter={(h) => `${String(h)}:00`}
                      />
                      <Legend />
                      <ReferenceLine y={0} stroke={COLORS.neutral} />
                      <Bar name="MAE" dataKey="mae" fill={COLORS.forecast} />
                      <Bar name="Bias" dataKey="bias" fill={COLORS.neutral} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>
            </div>
            <Panel
              title="Error by forecast lead time (all forecast runs)"
              subtitle={
                data.decisionHorizonMin === null || data.decisionHorizonMax === null
                  ? 'How accuracy changes as delivery approaches.'
                  : `How accuracy changes as delivery approaches. Dark bars: lead times of your decision-time forecast (${hours(data.decisionHorizonMin)}–${hours(data.decisionHorizonMax)}).`
              }
            >
              <div className="h-64">
                <ResponsiveContainer>
                  <BarChart
                    data={data.byHorizon.map((h) => ({
                      ...h,
                      label: `${h.lowerHours}–${h.upperHours} h`,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" />
                    <YAxis tickFormatter={gw} />
                    <Tooltip formatter={(v) => mw(Number(v))} />
                    <Bar name="MAE" dataKey="mae">
                      {data.byHorizon.map((h) => (
                        <Cell
                          key={h.lowerHours}
                          fill={
                            inDecisionRange(h.lowerHours, h.upperHours)
                              ? COLORS.forecast
                              : COLORS.otherRun
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <Panel title="Error by delivery day" subtitle="Click a bar to open that day.">
              <div className="h-64">
                <ResponsiveContainer>
                  <BarChart data={data.byDay}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="key" tickFormatter={(d: string) => d.slice(8)} />
                    <YAxis tickFormatter={gw} />
                    <Tooltip formatter={(v) => mw(Number(v))} />
                    <Legend />
                    <ReferenceLine y={0} stroke={COLORS.neutral} />
                    <Bar
                      name="MAE"
                      dataKey="mae"
                      fill={COLORS.forecast}
                      cursor="pointer"
                      onClick={(entry) =>
                        onSelectDay(String((entry as { payload?: { key?: string } }).payload?.key))
                      }
                    />
                    <Bar name="Bias" dataKey="bias" fill={COLORS.neutral} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
          </div>
        );
      }}
    </Loadable>
  );
}
