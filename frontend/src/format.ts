const UK = 'Europe/London';

const timeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: UK,
  hour: '2-digit',
  minute: '2-digit',
});
const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: UK,
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});
const dateFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: UK,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});
const number = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });

export const ukTime = (iso: string | number) => timeFormat.format(new Date(iso));
export const ukDateTime = (iso: string | number) => dateTimeFormat.format(new Date(iso));
export const longDate = (isoDate: string) => dateFormat.format(new Date(`${isoDate}T12:00:00Z`));
export const mw = (value: number) => `${number.format(value)} MW`;
export const signedMw = (value: number) => `${value > 0 ? '+' : ''}${number.format(value)} MW`;
export const hours = (value: number) => `${Number.isInteger(value) ? value : value.toFixed(1)} h`;

export function addDays(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
