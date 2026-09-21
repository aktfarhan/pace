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
export const CHIP = `${SHELL} px-2.25 py-1 font-mono text-chip uppercase`;

// The chip that opens a list
export const OPENER = `${CHIP} flex cursor-pointer items-center gap-1.5`;

// One row in an open list
export const OPTION =
    'flex cursor-pointer items-center rounded-chip px-2 py-1.25 font-mono text-chip uppercase transition-colors hover:bg-field';

// One pick inside a raised control
export const SEGMENT = 'cursor-pointer rounded-chip px-1.75 py-0.5 font-mono text-chip uppercase';

// When no branch is picked
export const EVERY = 'All';

// The longest branch name
export const SHORT_CODE = 4;
