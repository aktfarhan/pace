import { drawerOpen } from '@/hooks/useDrawer';
import { NAV } from '@/components/layout/sidebar/tints';
import type { Page } from '@/components/layout/sidebar/tints';

// The pages the number keys switch to
const KEYED: Page[] = NAV.map(({ label }) => label);

// The page a number key switches to
export function keyedPage(key: string): Page | undefined {
    return KEYED[Number(key) - 1];
}

// Keys with a modifier, typed in the text box, or the drawer's
export function claimed(event: KeyboardEvent) {
    if (event.metaKey || event.ctrlKey || event.altKey) return true;
    return event.target instanceof HTMLInputElement || drawerOpen();
}
