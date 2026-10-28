import { AUCTION_REFERENCES, CUTOFF_OPTIONS } from '../cutoffs';

interface Props {
  value: string | null;
  onChange: (cutoff: string) => void;
}

export function CutoffPicker({ value, onChange }: Props) {
  const reference = AUCTION_REFERENCES.find((r) => r.time === value);
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="cutoff" className="text-xs font-medium text-slate-300">
        Decision cutoff (UK time, day before delivery)
      </label>
      <select
        id="cutoff"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white"
      >
        <option value="" disabled>
          Select a cutoff…
        </option>
        {CUTOFF_OPTIONS.map(({ time, reference: ref }) => (
          <option key={time} value={time}>
            {ref ? `${time} — ${ref.label}` : time}
          </option>
        ))}
      </select>
      {reference && (
        <a
          href={reference.sourceUrl}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-sky-300 underline"
        >
          Source: {new URL(reference.sourceUrl).hostname}
        </a>
      )}
    </div>
  );
}
