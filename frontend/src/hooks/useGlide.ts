import { useLayoutEffect, useRef } from 'react';

// Clips a picked-look copy to the picked item for a glide effect
export function useGlide<Row extends HTMLElement = HTMLDivElement>(
    picked: unknown,
    spread = 0,
    round = '9999px',
) {
    const rowRef = useRef<Row>(null);
    const glideRef = useRef<HTMLDivElement>(null);

    useLayoutEffect(() => {
        const box = rowRef.current;
        const copy = glideRef.current;
        if (box === null || copy === null) return;

        // The copy shows only the picked item and its ring
        const place = () => {
            const items = [...box.querySelectorAll<HTMLElement>('[data-picked]')];
            const clone = copy.children[items.findIndex((item) => item.dataset.picked === 'true')];

            // A page outside the list leaves nothing picked 
            copy.style.opacity = clone === undefined ? '0' : '';
            if (clone === undefined) return;

            // The picked item's clone
            const frame = copy.getBoundingClientRect();
            const edge = clone.getBoundingClientRect();

            // Each side's crop leaves just the picked item + the spread
            const top = edge.top - frame.top - spread;
            const left = edge.left - frame.left - spread;
            const right = frame.right - edge.right - spread;
            const bottom = frame.bottom - edge.bottom - spread;
            copy.style.clipPath = `inset(${top}px ${right}px ${bottom}px ${left}px round ${round})`;
        };

        // Moves without a glide
        const snap = () => {
            copy.style.transition = 'none';
            place();
            copy.getBoundingClientRect();
            copy.style.transition = '';
        };

        // Coming back from nothing picked appears in place
        if (copy.style.opacity === '0') snap();
        else place();

        // A hidden box sends no first report
        let noted = box.getClientRects().length === 0;

        // Layout moves settle at once
        const watch = new ResizeObserver(() => {
            if (!noted) {
                noted = true;
                return;
            }
            snap();
        });
        watch.observe(box);

        // Items can shift inside a box that keeps its size
        box.querySelectorAll('[data-picked]').forEach((item) =>
            watch.observe(item, { box: 'border-box' }),
        );

        return () => watch.disconnect();
    }, [picked, round, spread]);

    return { rowRef, glideRef };
}
