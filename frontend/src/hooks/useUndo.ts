import { useCallback, useEffect, useRef, useState } from 'react';

// How long a removal can be undone
export const UNDO_MS = 5000;

// Waits before removing so it can be undone
export function useUndo() {
    const [pending, setPending] = useState(false);
    const timer = useRef(0);
    const armed = useRef<(() => void) | null>(null);

    // Removes now
    const fire = useCallback(() => {
        window.clearTimeout(timer.current);
        const run = armed.current;
        armed.current = null;
        setPending(false);
        run?.();
    }, []);

    const start = (commit: () => void) => {
        armed.current = commit;
        setPending(true);
        timer.current = window.setTimeout(fire, UNDO_MS);
    };

    const undo = () => {
        window.clearTimeout(timer.current);
        armed.current = null;
        setPending(false);
    };

    // Leaving the page removes right away
    useEffect(() => {
        window.addEventListener('pagehide', fire);
        return () => {
            window.removeEventListener('pagehide', fire);
            fire();
        };
    }, [fire]);

    return { pending, start, undo };
}
