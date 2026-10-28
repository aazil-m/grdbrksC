// Decision cutoff options: 30-minute steps plus sourced GB day-ahead auction gate closures.

export interface AuctionReference {
  time: string;
  label: string;
  sourceUrl: string;
}

export const AUCTION_REFERENCES: AuctionReference[] = [
  {
    time: '09:20',
    label: 'EPEX SPOT GB 60-min day-ahead auction closes',
    sourceUrl: 'https://www.epexspot.com/en/news/spot-power-market-arrangements-under-brexit',
  },
  {
    time: '09:50',
    label: 'Nord Pool N2EX GB day-ahead auction closes',
    sourceUrl:
      'https://support.nordpoolgroup.com/support/solutions/articles/8000088463-about-the-day-ahead-gb-auction',
  },
  {
    time: '15:30',
    label: 'EPEX SPOT GB 30-min day-ahead auction closes',
    sourceUrl: 'https://www.epexspot.com/en/news/spot-power-market-arrangements-under-brexit',
  },
];

export interface CutoffOption {
  time: string;
  reference?: AuctionReference;
}

function halfHourSteps(): string[] {
  return Array.from({ length: 48 }, (_, i) => {
    const hours = String(Math.floor(i / 2)).padStart(2, '0');
    return `${hours}:${i % 2 === 0 ? '00' : '30'}`;
  });
}

export const CUTOFF_OPTIONS: CutoffOption[] = [
  ...new Set([...halfHourSteps(), ...AUCTION_REFERENCES.map((r) => r.time)]),
]
  .sort()
  .map((time) => ({ time, reference: AUCTION_REFERENCES.find((r) => r.time === time) }));
