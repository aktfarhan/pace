import { LINES, type LineLabel } from '@/lib/lines';

export type Tab = 'All' | LineLabel;

// The tab row
export const TABS: { label: Tab; dot: string | null }[] = [
    { label: 'All', dot: null },
    ...LINES.map(({ label, fill }) => ({ label, dot: fill })),
];

// The chart's small controls
export const SHELL = 'rounded-chip border border-edge bg-bubble';

// A label for the chart's corners
export const CHIP = `${SHELL} px-2.25 py-0.75 font-mono text-chip uppercase`;

// One pick inside a raised control
export const SEGMENT = 'cursor-pointer rounded-chip px-1.75 py-0.5 font-mono text-chip uppercase';

// When no branch is picked
export const EVERY = 'All';
