import Axis from './Axis';
import { seriesOf } from './plot';
import { windowOf } from './frame';
import { LINES } from '@/lib/lines';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { Box } from './plot';
import type { Reading } from '@/types/transit';

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

interface ChartProps {
    series: Record<string, Reading[]>;
    read: number;
}

function Chart({ series, read }: ChartProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);

    const { start, end } = useMemo(() => {
        const days = LINES.map((line) => series[line.id] ?? []);
        return windowOf(read, days);
    }, [read, series]);

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

    // Place the readings only when they or the box move
    const drawn = useMemo(
        () =>
            LINES.map((line) => ({
                line,
                ...seriesOf(series[line.id] ?? [], start, end, box),
            })),
        [series, start, end, box],
    );

    return (
        <div ref={cardRef} className="rounded-tile border border-seam bg-panel px-6 pt-5 pb-4">
            <div style={{ height: HEIGHT }}>
                {width > 0 && (
                    <svg
                        role="img"
                        aria-label="How late each line has been running today"
                        viewBox={`0 0 ${width} ${HEIGHT}`}
                        className="block w-full overflow-visible"
                    >
                        <Axis box={box} start={start} end={end} />
                        {drawn.map((one) => (
                            <path
                                key={one.line.id}
                                d={one.path}
                                fill="none"
                                strokeWidth={1.75}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className={one.line.stroke}
                            />
                        ))}
                    </svg>
                )}
            </div>
        </div>
    );
}

export default Chart;
