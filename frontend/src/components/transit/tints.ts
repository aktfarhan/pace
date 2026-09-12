import { LINES, type LineLabel } from '@/lib/lines';

export type Tab = 'All' | LineLabel;

// The tab row
export const TABS: { label: Tab; dot: string | null }[] = [
    { label: 'All', dot: null },
    ...LINES.map(({ label, fill }) => ({ label, dot: fill })),
];
