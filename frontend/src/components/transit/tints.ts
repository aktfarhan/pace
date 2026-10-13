import { LINES, type LineLabel } from '@/lib/lines';

export type Tab = 'All' | LineLabel;

// The tab row
export const TABS: { label: Tab; dot: string | null }[] = [
    { label: 'All', dot: null },
    ...LINES.map(({ label, fill }) => ({ label, dot: fill })),
];

// When no branch is picked
export const EVERY = 'All';

// The longest branch name
export const SHORT_CODE = 4;

// The chart's card
export const CARD =
    'flex flex-col gap-3 rounded-tile border border-seam bg-panel px-6 pt-5 pb-4 shadow-card';
