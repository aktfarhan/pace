import { still } from '@/lib/device';
import { useEffect, useEffectEvent } from 'react';
import type { RefObject } from 'react';

// A swipe this fast closes it
const FLICK = 0.11;

// Movement before a touch counts as a swipe
const SLOP = 10;

// How far back a swipe's speed is measured
const TRAIL_MS = 100;

// A swipe this share of the drawer's width closes it
const FAR = 1 / 3;

// Swiping left drags the drawer; a long or quick swipe closes it
export function useSwipeAway(
    panelRef: RefObject<HTMLElement | null>,
    scrimRef: RefObject<HTMLElement | null>,
    open: boolean,
    close: () => void,
) {
    const dismiss = useEffectEvent(close);

    useEffect(() => {
        const panel = panelRef.current;
        const scrim = scrimRef.current;
        if (!open || panel === null || scrim === null) return;

        let from = { x: 0, y: 0, id: -1 };

        // Track recent finger positions
        let trail: { x: number; at: number }[] = [];
        let pull = 0;
        let width = 0;
        let state: 'idle' | 'watching' | 'dragging' = 'idle';
        let held = false;

        // Clears the swipe's inline styles
        const release = () => {
            panel.style.transition = '';
            panel.style.translate = '';
            scrim.style.transition = '';
            scrim.style.opacity = '';
        };

        // Undo a reduced-motion swipe's offset without sliding
        if (panel.style.translate !== '') {
            panel.style.transitionProperty = 'opacity';
            panel.style.translate = '';
            void panel.offsetWidth;
            panel.style.transitionProperty = '';
        }

        // A second mid-swipe is ignored
        const down = (event: PointerEvent) => {
            if (event.pointerType === 'mouse' || state !== 'idle') return;
            from = { x: event.clientX, y: event.clientY, id: event.pointerId };
            trail = [{ x: event.clientX, at: event.timeStamp }];
            state = 'watching';
        };

        const move = (event: PointerEvent) => {
            if (state === 'idle' || event.pointerId !== from.id) return;
            const x = event.clientX - from.x;
            const y = event.clientY - from.y;

            if (state === 'watching') {
                // Wait for a proper swipe
                if (Math.abs(x) < SLOP && Math.abs(y) < SLOP) return;
                if (Math.abs(y) > Math.abs(x) || x > 0) {
                    state = 'idle';
                    return;
                }
                state = 'dragging';

                // Measured once
                width = panel.offsetWidth;
                panel.style.transition = 'none';
                scrim.style.transition = 'none';
            }

            // Keep only the recent positions
            trail = [
                ...trail.filter((one) => event.timeStamp - one.at < TRAIL_MS),
                { x: event.clientX, at: event.timeStamp },
            ];

            // Move the drawer and dim layer behind
            pull = Math.min(0, x);
            panel.style.translate = `${pull}px 0`;
            scrim.style.opacity = String(1 + pull / width);
        };

        const up = (event: PointerEvent) => {
            if (event.pointerId !== from.id) return;

            // End the tap
            const dragged = state === 'dragging';
            state = 'idle';
            if (!dragged) return;

            // Speed over the last moves
            const first = trail.find((one) => event.timeStamp - one.at < TRAIL_MS);
            const speed =
                first === undefined ? 0 : (first.x - event.clientX) / (event.timeStamp - first.at);
            const going = pull < -width * FAR || speed > FLICK;
            release();
            if (!going) return;

            // Reduced motion fades it out
            held = still();
            panel.style.translate = held ? `${pull}px 0` : '-100% 0';
            dismiss();
        };

        // If the browser takes the gesture over
        const cancel = (event: PointerEvent) => {
            if (event.pointerId !== from.id) return;
            state = 'idle';
            release();
        };

        panel.addEventListener('pointerdown', down);
        panel.addEventListener('pointermove', move);
        panel.addEventListener('pointerup', up);
        panel.addEventListener('pointercancel', cancel);
        return () => {
            if (!held) release();
            panel.removeEventListener('pointerdown', down);
            panel.removeEventListener('pointermove', move);
            panel.removeEventListener('pointerup', up);
            panel.removeEventListener('pointercancel', cancel);
        };
    }, [panelRef, scrimRef, open]);
}
