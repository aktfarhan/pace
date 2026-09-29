import { useEffect, useRef, useState } from 'react';
import type { FocusEvent, KeyboardEvent, PointerEvent } from 'react';

// The first tip takes time to load
const WAIT_MS = 400;
const WARM_MS = 300;

// The tip's gap from the sidebar
const GAP = 10;

// When the last tip closed
let closed = 0;

// Where a tip sits, and whether it skips load time
interface Spot {
    x: number;
    y: number;
    instant: boolean;
}

export function useTip() {
    const [spot, setSpot] = useState<Spot | null>(null);
    const timer = useRef(0);

    // Opens the tip beside its button
    const open = (trigger: HTMLElement, now: boolean) => {
        // Centered to the right of the button
        const box = trigger.getBoundingClientRect();
        const at = { x: box.right + GAP, y: box.top + box.height / 2 };

        // Cancels a tip that hasn't opened yet
        window.clearTimeout(timer.current);

        // No load time for the keyboard, or when moving between tips
        if (now || performance.now() - closed < WARM_MS) {
            setSpot({ ...at, instant: true });
            return;
        }

        // Otherwise waits the load time
        timer.current = window.setTimeout(() => setSpot({ ...at, instant: false }), WAIT_MS);
    };

    // Hides the tip and saves when it closed
    const close = () => {
        window.clearTimeout(timer.current);
        if (spot !== null) closed = performance.now();
        setSpot(null);
    };

    // Cancels the wait when the button goes away
    useEffect(() => () => window.clearTimeout(timer.current), []);

    const handlers = {
        // Opens on mouse hover
        onPointerEnter: (event: PointerEvent<HTMLElement>) => {
            if (event.pointerType !== 'touch') open(event.currentTarget, false);
        },

        // Closes when the mouse leaves or clicks
        onPointerLeave: close,
        onPointerDown: close,

        // Opens when tabbed to with the keyboard
        onFocus: (event: FocusEvent<HTMLElement>) => {
            if (event.target.matches(':focus-visible')) open(event.currentTarget, true);
        },
        onBlur: close,

        // Closes on Escape
        onKeyDown: (event: KeyboardEvent<HTMLElement>) => {
            if (event.key === 'Escape') close();
        },
    };

    return { spot, handlers };
}
