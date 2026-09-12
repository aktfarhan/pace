import { Bookmark, Clock, MessageSquare, TrainFront } from 'lucide-react';
import type { Chip, State } from '@/types/status';

// The pages the sidebar switches between
export type Page = 'Ask' | 'Transit' | 'History' | 'Saved';

// The tabs both sidebar states list
export const NAV: { label: Page; Icon: typeof MessageSquare }[] = [
    { label: 'Ask', Icon: MessageSquare },
    { label: 'Transit', Icon: TrainFront },
    { label: 'History', Icon: Clock },
    { label: 'Saved', Icon: Bookmark },
];

// The card, tinted once a line stops running
export const CARDS: Record<State, string> = {
    clear: 'border-seam bg-panel',
    notice: 'border-seam bg-panel',
    disrupted: 'border-amber/16 bg-amber/5',
    severe: 'border-red-fill/26 bg-red-fill/7',
};

// The pill in place of a delay figure
export const PILLS: Record<Exclude<State, 'clear'>, string> = {
    notice: 'border-seam bg-field text-hush',
    disrupted: 'border-amber/28 bg-amber/10 text-amber',
    severe: 'border-red-fill/28 bg-red-fill/14 text-red',
};

// A chip: read for the fact, quiet for the other, dashed for a placeholder
export const CHIPS: Record<Chip['tone'], string> = {
    read: 'border-seam text-dim',
    quiet: 'border-seam text-faint',
    blank: 'border-dashed border-line text-ghost',
};
