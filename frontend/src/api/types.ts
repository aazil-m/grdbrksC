// Mirrors backend/app/schemas.py. Times are UTC ISO-8601 strings; power is MW.

export interface Health {
  status: string;
  firstDay: string;
  lastDay: string;
}

export interface ActualPoint {
  start: string;
  generation: number;
}

export interface ForecastPoint {
  start: string;
  actual: number | null;
  forecast: number | null;
  publishTime: string | null;
  horizonHours: number | null;
  /** forecast − actual (MW). Positive: forecast too high. */
  error: number | null;
}

export interface Summary {
  count: number;
  mae: number;
  rmse: number;
  bias: number;
  nmaePct: number | null;
  p10: number;
  p50: number;
  p90: number;
  maxAbsError: number;
}

export interface DayResponse {
  date: string;
  cutoff: string;
  cutoffUtc: string;
  actuals: ActualPoint[];
  points: ForecastPoint[];
  missingHours: number;
  summary: Summary | null;
}

export interface Run {
  publishTime: string;
  isDecisionRun: boolean;
  points: ActualPoint[];
}

export interface VintagesResponse {
  date: string;
  cutoff: string;
  cutoffUtc: string;
  actuals: ActualPoint[];
  runs: Run[];
}

export interface Bin {
  lower: number;
  upper: number;
  count: number;
}

export interface GroupStat {
  key: string;
  count: number;
  mae: number;
  bias: number;
}

export interface HorizonStat {
  lowerHours: number;
  upperHours: number;
  count: number;
  mae: number;
  rmse: number;
  bias: number;
}

export interface MetricsResponse {
  cutoff: string;
  summary: Summary | null;
  totalHours: number;
  missingHours: number;
  decisionHorizonMin: number | null;
  decisionHorizonMax: number | null;
  histogram: Bin[];
  byHourOfDay: GroupStat[];
  byDay: GroupStat[];
  byHorizon: HorizonStat[];
}
