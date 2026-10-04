export const colors = {
  primary: '#7A1F3D',
  primaryDark: '#5C1630',
  primarySoft: '#F6E9EE',
  rose: '#E3B4C2',
  accent: '#2F3E6B',
  accentSoft: '#E8EBF3',
  gold: '#C8963E',
  goldSoft: '#F7EEDC',
  bg: '#F8F5F2',
  card: '#FFFFFF',
  text: '#1F2933',
  muted: '#6B7280',
  border: '#E8E2DD',
  danger: '#B42318',
} as const;

// One colour per line of the breakdown, in a fixed order that alternates dark and light
// so neighbouring segments stay distinguishable. No green or red: those read as good/bad.
export const series: Record<string, string> = {
  income: '#7A1F3D',
  mortgage: '#C8963E',
  debts: '#2F3E6B',
  education: '#8FB0D9',
  final: '#9A938C',
  savings: '#B8869A',
  existing_coverage: '#E3B4C2',
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 } as const;
export const radius = 14;
export const font = { small: 14, body: 16, title: 20, hero: 40 } as const;

/** Soft card shadow (iOS shadow* and Android elevation). */
export const shadow = {
  shadowColor: '#3B1020',
  shadowOpacity: 0.08,
  shadowRadius: 12,
  shadowOffset: { width: 0, height: 4 },
  elevation: 2,
} as const;

const dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

export function formatUSD(amount: number): string {
  return dollars.format(amount);
}

/** Short form for chart labels: $1.6M, $240K. */
export function formatShortUSD(amount: number): string {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `$${Math.round(amount / 1_000)}K`;
  return formatUSD(amount);
}
