import { useMemo } from 'react';
import { useWidth } from '@/hooks/useWidth';
import type { Box } from './plot';

// How tall the drawing is
const HEIGHT = 278;

// The edges the plot draws between
const FLOOR = 246;
const CEIL = 16;

// Below this width the margins tighten
const TIGHT = 380;

// Extra height for wide charts
const WIDE = 560;
const TALLER = 40;

// Room left for the share labels, and a right gutter
const LEFT = 48;
const TIGHT_LEFT = 34;
const GUTTER = 16;
const TIGHT_GUTTER = 12;

export function useChartBox() {
    const [cardRef, width] = useWidth<HTMLDivElement>();
    const tight = width < TIGHT;
    const taller = width >= WIDE ? TALLER : 0;

    const box: Box = useMemo(
        () => ({
            left: tight ? TIGHT_LEFT : LEFT,
            right: width - (tight ? TIGHT_GUTTER : GUTTER),
            floor: FLOOR + taller,
            ceil: CEIL,
        }),
        [width, tight, taller],
    );

    return { cardRef, width, box, height: HEIGHT + taller, tight };
}
