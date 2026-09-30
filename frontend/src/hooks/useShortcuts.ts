import { drawerOpen } from './useDrawer';
import { NAV } from '@/components/layout/sidebar/tints';
import { useEffect, useEffectEvent, useRef } from 'react';
import type { Page } from '@/components/layout/sidebar/tints';

// How long a keyed switch holds the highlight
const JUMP_MS = 250;

// The pages the number keys switch to
const KEYED: Page[] = NAV.map(({ label }) => label);

// Number keys switch pages, and '/' opens the ask box
export function useShortcuts(go: (page: Page) => void, ask: () => void) {
    // The timer that lets the highlight glide again
    const jumping = useRef(0);

    const press = useEffectEvent((event: KeyboardEvent) => {
        // Skips keys used with modifiers or typed in the text box
        if (event.metaKey || event.ctrlKey || event.altKey) return;
        if (event.target instanceof HTMLInputElement) return;

        // The open drawer keeps its keys to itself
        if (drawerOpen()) return;

        // The page a number key switches to
        const page: Page | undefined = KEYED[Number(event.key) - 1];
        if (page !== undefined) {
            // Instant switch
            document.documentElement.toggleAttribute('data-keyed', true);
            go(page);

            // Goes back to glide switch
            window.clearTimeout(jumping.current);
            jumping.current = window.setTimeout(
                () => document.documentElement.removeAttribute('data-keyed'),
                JUMP_MS,
            );
        } else if (event.key === '/') {
            event.preventDefault();
            ask();
        }
    });

    // Listens for keys anywhere on the page
    useEffect(() => {
        window.addEventListener('keydown', press);
        return () => window.removeEventListener('keydown', press);
    }, []);
}
