import type { DayResponse, Health, MetricsResponse, VintagesResponse } from './types';

async function getJson<T>(
  path: string,
  params: Record<string, string>,
  signal: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(query ? `${path}?${query}` : path, { signal });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  health: (signal: AbortSignal) => getJson<Health>('/api/health', {}, signal),
  day: (date: string, cutoff: string, signal: AbortSignal) =>
    getJson<DayResponse>('/api/day', { date, cutoff }, signal),
  vintages: (date: string, cutoff: string, signal: AbortSignal) =>
    getJson<VintagesResponse>('/api/vintages', { date, cutoff }, signal),
  metrics: (cutoff: string, signal: AbortSignal) =>
    getJson<MetricsResponse>('/api/metrics', { cutoff }, signal),
};
