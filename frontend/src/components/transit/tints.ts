import { LINES, type LineLabel } from '@/lib/lines';

export type Tab = 'All' | LineLabel;

// The tab row
export const TABS: { label: Tab; dot: string | null }[] = [
    { label: 'All', dot: null },
    ...LINES.map(({ label, fill }) => ({ label, dot: fill })),
];

// The chart's small controls
const SHELL = 'rounded-chip border border-edge bg-bubble';

// A label for the chart's corners
export const CHIP = `${SHELL} px-2.25 py-0.75 font-mono text-chip uppercase`;
