import Axis from './Axis';
import Ends from './Ends';
import Guide from './Guide';
import Labels from './Labels';
import Legend from './Legend';
import { useMemo } from 'react';
import { windowOf } from './frame';
import { LINES } from '@/lib/lines';
import { figuresOf } from './figures';
import { useHover } from '@/hooks/useHover';
import { useChartBox } from '@/hooks/useChartBox';
import { useEmphasis } from '@/hooks/useEmphasis';
import { marksOf, nearestOf, seriesOf, stackOf } from './plot';
import type { Reading } from '@/types/transit';

interface ChartProps {
    series: Record<string, Reading[]>;
    read: number;
}

function Chart({ series, read }: ChartProps) {
    const { cardRef, width, box, height, tight } = useChartBox();

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
    const { held, reading, follow, lift, clear } = useHover(sheets, shown, start, end, box);

    const marks = marksOf(drawn, reading);

    const near = held === null ? null : nearestOf(marks, held.y);
    const { picked, lead, strengthOf, toggle, light } = useEmphasis(near);

    const labels = stackOf(marks, box.floor);
    const guide = marks.length === 0 ? null : marks[0].spot;

    const figures = useMemo(() => figuresOf(series), [series]);

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
            <Legend
                figures={figures}
                picked={picked}
                strengthOf={strengthOf}
                light={light}
                toggle={toggle}
            />
            <div className="mt-3" style={{ height }}>
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
                        {guide !== null && <Guide spot={guide} box={box} />}
                        {drawn.map((one) => (
                            <path
                                key={one.line.id}
                                d={one.path}
                                fill="none"
                                strokeWidth={lead === one.line.id ? 2.75 : 1.75}
                                strokeOpacity={strengthOf(one.line.id)}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className={one.line.stroke}
                            />
                        ))}
                        <Ends ends={ends} strengthOf={strengthOf} />
                        <Labels labels={labels} box={box} tight={tight} />
                    </svg>
                )}
            </div>
        </div>
    );
}

export default Chart;
