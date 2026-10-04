export const colors = {
  primary: '#7A1F3D',
  primaryDark: '#5C1630',
  accent: '#F2622E',
  bg: '#FAF7F5',
  card: '#FFFFFF',
  text: '#1F2933',
  muted: '#6B7280',
  border: '#E8E2DD',
  success: '#1F7A6B',
  successSoft: '#E3F2EF',
  primarySoft: '#F6E9EE',
  danger: '#B42318',
} as const;

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 } as const;
export const radius = 12;
export const font = { small: 14, body: 16, title: 20, hero: 34 } as const;

const dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

export function formatUSD(amount: number): string {
  return dollars.format(amount);
}
