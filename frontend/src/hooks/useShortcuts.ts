import { claimed, keyedPage } from '@/lib/keys';
import { useEffect, useEffectEvent, useRef } from 'react';
import type { Page } from '@/components/layout/sidebar/tints';

// How long a keyed switch holds the highlight
const JUMP_MS = 250;

// Number keys switch pages
export function useShortcuts(go: (page: Page) => void) {
    // The timer that lets the highlight glide again
    const jumping = useRef(0);

    const press = useEffectEvent((event: KeyboardEvent) => {
        // Skip keys claimed by modifiers
        if (claimed(event)) return;

        // The page a number key switches to
        const page = keyedPage(event.key);
        if (page !== undefined) {
            event.preventDefault();

            // Instant switch
            document.documentElement.toggleAttribute('data-keyed', true);
            go(page);

            // Goes back to glide switch
            window.clearTimeout(jumping.current);
            jumping.current = window.setTimeout(
                () => document.documentElement.removeAttribute('data-keyed'),
                JUMP_MS,
            );
        }
    });

    // Listens for keys anywhere on the page
    useEffect(() => {
        window.addEventListener('keydown', press);
        return () => window.removeEventListener('keydown', press);
    }, []);
}
