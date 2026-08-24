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

// The badge each line has
export const BADGES: Record<string, string> = {
    Red: 'border-red-fill/28 bg-red-fill/12 text-red',
    Orange: 'border-orange-fill/28 bg-orange-fill/12 text-orange',
    Green: 'border-green-fill/28 bg-green-fill/12 text-green',
    Blue: 'border-blue-fill/28 bg-blue-fill/12 text-blue',
    CR: 'border-commuter-fill/28 bg-commuter-fill/12 text-commuter',
};

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

// The tag a line has once the sidebar collapses
export const TAGS: Record<string, string> = {
    Red: 'border-red-fill/26 bg-red-fill/12 text-red',
    Orange: 'border-orange-fill/26 bg-orange-fill/12 text-orange',
    Green: 'border-green-fill/26 bg-green-fill/12 text-green',
    Blue: 'border-blue-fill/26 bg-blue-fill/12 text-blue',
    CR: 'border-commuter-fill/26 bg-commuter-fill/12 text-commuter',
};

// The same tag once the line is hit
export const TAGS_HIT: Record<string, string> = {
    Red: 'border-red-fill/40 bg-red-fill/12 text-red',
    Orange: 'border-orange-fill/40 bg-orange-fill/12 text-orange',
    Green: 'border-green-fill/40 bg-green-fill/12 text-green',
    Blue: 'border-blue-fill/40 bg-blue-fill/12 text-blue',
    CR: 'border-commuter-fill/40 bg-commuter-fill/12 text-commuter',
};
