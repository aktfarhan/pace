import { useLayoutEffect, useRef } from 'react';

// Clips a picked-look copy to the picked item for a glide effect
export function useGlide<Row extends HTMLElement = HTMLDivElement>(
    picked: unknown,
    spread: number,
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
            const on = box.querySelector<HTMLElement>('[data-picked="true"]');
            if (on === null) return;

            // Each side's crop leaves just the picked item + the spread
            const top = on.offsetTop - spread;
            const left = on.offsetLeft - spread;
            const right = box.clientWidth - on.offsetLeft - on.offsetWidth - spread;
            const bottom = box.clientHeight - on.offsetTop - on.offsetHeight - spread;
            copy.style.clipPath = `inset(${top}px ${right}px ${bottom}px ${left}px round ${round})`;
        };

        // Moves without a glide
        const snap = () => {
            copy.style.transition = 'none';
            place();
            copy.getBoundingClientRect();
            copy.style.transition = '';
        };

        place();

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
