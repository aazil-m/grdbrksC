import { addDays, longDate } from '../format';

interface Props {
  value: string;
  min: string;
  max: string;
  onChange: (date: string) => void;
}

export function DayPicker({ value, min, max, onChange }: Props) {
  const button =
    'rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-40';
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        className={button}
        disabled={value <= min}
        onClick={() => onChange(addDays(value, -1))}
      >
        ◀ Previous
      </button>
      <input
        type="date"
        aria-label="Delivery day"
        value={value}
        min={min}
        max={max}
        onChange={(event) => event.target.value && onChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
      />
      <button
        className={button}
        disabled={value >= max}
        onClick={() => onChange(addDays(value, 1))}
      >
        Next ▶
      </button>
      <span className="text-sm text-slate-600">Delivery day: {longDate(value)}</span>
    </div>
  );
}
