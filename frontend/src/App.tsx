import { lazy, Suspense, useState } from 'react';

import { api } from './api/client';
import { useApi } from './api/useApi';
import { CutoffPicker } from './components/CutoffPicker';
import { DayPicker } from './components/DayPicker';
import { Loadable } from './components/ui';

// Views (and the charting library) load on demand after a cutoff is chosen.
const AccuracyView = lazy(() =>
  import('./views/AccuracyView').then((m) => ({ default: m.AccuracyView })),
);
const DecisionDayView = lazy(() =>
  import('./views/DecisionDayView').then((m) => ({ default: m.DecisionDayView })),
);
const VintagesView = lazy(() =>
  import('./views/VintagesView').then((m) => ({ default: m.VintagesView })),
);

const TABS = [
  { id: 'day', label: 'Decision day' },
  { id: 'vintages', label: 'Forecast vintages' },
  { id: 'accuracy', label: 'Accuracy' },
] as const;
type Tab = (typeof TABS)[number]['id'];

function App() {
  const health = useApi('health', (signal) => api.health(signal));
  const [cutoff, setCutoff] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('day');
  const [date, setDate] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-xl font-semibold">UK Wind Forecast Monitor</h1>
            <p className="text-sm text-slate-300">
              Day-ahead wind forecasts vs actual generation · Elexon BMRS · decisions made January
              2026
            </p>
          </div>
          <CutoffPicker value={cutoff} onChange={setCutoff} />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <Loadable state={health}>
          {({ firstDay, lastDay }) => {
            const day = date ?? firstDay;
            if (cutoff === null) {
              return (
                <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
                  <h2 className="text-lg font-semibold">Choose your decision cutoff to begin</h2>
                  <p className="mx-auto mt-2 max-w-xl text-sm text-slate-600">
                    The cutoff is the time on the day before delivery when you place your day-ahead
                    purchases. Every view shows only the wind forecast that was published by then.
                  </p>
                </div>
              );
            }
            return (
              <>
                <nav className="mb-4 flex gap-1 border-b border-slate-200" role="tablist">
                  {TABS.map(({ id, label }) => (
                    <button
                      key={id}
                      role="tab"
                      aria-selected={tab === id}
                      onClick={() => setTab(id)}
                      className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
                        tab === id
                          ? 'border-blue-600 text-blue-700'
                          : 'border-transparent text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </nav>
                {tab !== 'accuracy' && (
                  <div className="mb-4">
                    <DayPicker value={day} min={firstDay} max={lastDay} onChange={setDate} />
                  </div>
                )}
                <Suspense
                  fallback={<p className="py-12 text-center text-sm text-slate-500">Loading…</p>}
                >
                  {tab === 'day' && <DecisionDayView date={day} cutoff={cutoff} />}
                  {tab === 'vintages' && <VintagesView date={day} cutoff={cutoff} />}
                  {tab === 'accuracy' && (
                    <AccuracyView
                      cutoff={cutoff}
                      onSelectDay={(selected) => {
                        setDate(selected);
                        setTab('day');
                      }}
                    />
                  )}
                </Suspense>
              </>
            );
          }}
        </Loadable>
      </main>
    </div>
  );
}

export default App;
