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

// A nav row
const TAB =
    'cursor-pointer transition-[color,background-color,scale] duration-150 ease-out active:scale-98';

// Focused tab
export const HERE = `${TAB} bg-accent/7 text-accent ring-1 ring-accent/16`;

// Away tab
export const AWAY = `${TAB} text-quiet hover:bg-accent/6 hover:text-cream`;

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

// A chip's text
export const CHIPS: Record<Chip['tone'], string> = {
    quiet: 'text-hush',
    blank: 'text-faint',
};

// Every page's icon as an outline
export const OUTLINED = { size: 20, strokeWidth: 1.8 };

// The picked look's corner
export const GLIDE_ROUND = 'calc(var(--radius-row) + 1px)';
