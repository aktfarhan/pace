import Axis from './Axis';
import Ends from './Ends';
import { seriesOf } from './plot';
import { windowOf } from './frame';
import { LINES } from '@/lib/lines';
import { useHover } from '@/hooks/useHover';
import { useChartBox } from '@/hooks/useChartBox';
import { useMemo } from 'react';
import type { Reading } from '@/types/transit';

interface ChartProps {
    series: Record<string, Reading[]>;
    read: number;
}

function Chart({ series, read }: ChartProps) {
    const { cardRef, width, box, height } = useChartBox();

    const { start, end } = useMemo(() => {
        const days = LINES.map((line) => series[line.id] ?? []);
        return windowOf(read, days);
    }, [read, series]);

    // Place the readings only when they or the box move
    const drawn = useMemo(
        () =>
            LINES.map((line) => ({
                line,
                ...seriesOf(series[line.id] ?? [], start, end, box),
            })),
        [series, start, end, box],
    );

    // The lines the hover reads from
    const shown = drawn.map((one) => one.line.id).join();
    const sheets = useMemo(() => drawn.map((one) => one.spots), [drawn]);
    const { follow, lift, clear } = useHover(sheets, shown, start, end, box);

    // Where each line has reached
    const ends = useMemo(
        () =>
            drawn
                .map((one) => {
                    const spot = one.spots.findLast((seen) => seen !== null);
                    return spot == null ? null : { id: one.line.id, stroke: one.line.stroke, spot };
                })
                .filter((one) => one !== null),
        [drawn],
    );

    return (
        <div ref={cardRef} className="rounded-tile border border-seam bg-panel px-6 pt-5 pb-4">
            <div style={{ height }}>
                {width > 0 && (
                    <svg
                        role="img"
                        aria-label="How late each line has been running today"
                        viewBox={`0 0 ${width} ${height}`}
                        className="block w-full touch-pan-y overflow-visible"
                        onPointerMove={follow}
                        onPointerUp={lift}
                        onPointerLeave={clear}
                        onPointerCancel={clear}
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
                        <Ends ends={ends} />
                    </svg>
                )}
            </div>
        </div>
    );
}

export default Chart;
