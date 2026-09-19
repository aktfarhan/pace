import { useEffect, useMemo, useRef, useState } from 'react';
import type { Box } from '@/components/transit/plot';

// How tall the drawing is
const HEIGHT = 278;

// The edges the plot draws between
const FLOOR = 246;
const CEIL = 16;

// Below this width the margins tighten
const TIGHT = 380;

// Room on the left for the share labels, and a gutter on the right
const LEFT = 48;
const TIGHT_LEFT = 34;
const GUTTER = 16;
const TIGHT_GUTTER = 12;

export function useChartBox() {
    const cardRef = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);

    // Follow the card so one unit stays one pixel
    useEffect(() => {
        const card = cardRef.current;
        if (card === null) return;

        const watch = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
        watch.observe(card);
        return () => watch.disconnect();
    }, []);

    const box: Box = useMemo(() => {
        const tight = width < TIGHT;
        return {
            left: tight ? TIGHT_LEFT : LEFT,
            right: width - (tight ? TIGHT_GUTTER : GUTTER),
            floor: FLOOR,
            ceil: CEIL,
        };
    }, [width]);

    return { cardRef, width, box, height: HEIGHT, tight: width < TIGHT };
}
