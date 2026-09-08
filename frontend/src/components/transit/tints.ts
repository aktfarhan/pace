export type Tab = 'All' | 'Red' | 'Orange' | 'Green' | 'Blue' | 'Commuter';

export const TABS: { label: Tab; dot: string | null }[] = [
    { label: 'All', dot: null },
    { label: 'Red', dot: 'bg-red-fill' },
    { label: 'Orange', dot: 'bg-orange-fill' },
    { label: 'Green', dot: 'bg-green-fill' },
    { label: 'Blue', dot: 'bg-blue-fill' },
    { label: 'Commuter', dot: 'bg-commuter-fill' },
];
