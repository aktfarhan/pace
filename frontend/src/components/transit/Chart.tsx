import Axis from './Axis';
import Ends from './Ends';
import Focus from './Focus';
import Heading from './Heading';
import Guide from './Guide';
import Labels from './Labels';
import Legend from './Legend';
import Typical from './Typical';
import { windowOf } from './frame';
import { figuresOf, typicalOf } from './figures';
import { useMemo, useState } from 'react';
import { useHover } from '@/hooks/useHover';
import { useChartBox } from '@/hooks/useChartBox';
import { useEmphasis } from '@/hooks/useEmphasis';
import { marksOf, nearestOf, seriesOf, stackOf, stretchedOf } from './plot';
import type { Drawn } from '@/lib/lines';
import type { Reading } from '@/types/transit';

interface ChartProps {
    lines: readonly Drawn[];
    series: Record<string, Reading[]>;
    typical: Record<string, Reading[]>;
    read: number;
    late: number;
    rolling: number;
}

function Chart({ lines, series, typical, read, late, rolling }: ChartProps) {
    const { cardRef, width, box, height, tight } = useChartBox();
    const [span, setSpan] = useState<number | null>(null);

    const { start, end } = useMemo(() => {
        const days = lines.map((line) => series[line.id]);
        return windowOf(read, days, span);
    }, [lines, read, series, span]);

    // Place the readings only when they or the box move
    const drawn = useMemo(
        () =>
            lines.map((line) => ({
                line,
                ...seriesOf(series[line.id], start, end, box),
            })),
        [lines, series, start, end, box],
    );

    // The lines the hover reads from
    const shown = drawn.map((one) => one.line.id).join();
    const sheets = useMemo(() => drawn.map((one) => one.spots), [drawn]);
    const { held, reading, follow, lift, clear } = useHover(sheets, shown, start, end, box);

    const marks = marksOf(drawn, reading);

    const near = held === null ? null : nearestOf(marks, held.y);
    const { picked, lead, strengthOf, toggle, light } = useEmphasis(shown, near);

    const labels = stackOf(marks, box.floor);
    const guide = marks.length === 0 ? null : marks[0].spot;

    const figures = useMemo(() => figuresOf(lines, series), [lines, series]);
    const typically = useMemo(() => typicalOf(typical, lines), [typical, lines]);

    // The typical is only for specific lines
    const typicalPath = useMemo(() => {
        if (lines.length !== 1) return null;

        const { path } = seriesOf(typical[lines[0].id], start, end, box);
        return path === '' ? null : { path, stroke: lines[0].stroke };
    }, [lines, typical, start, end, box]);
    const stretched = useMemo(() => stretchedOf(drawn, rolling), [drawn, rolling]);

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
        <div
            ref={cardRef}
            className="flex flex-col gap-3 rounded-tile border border-seam bg-panel px-6 pt-5 pb-4"
        >
            <Heading late={late} stretched={stretched} tight={tight} span={span} select={setSpan} />
            {figures.length === 1 ? (
                <Focus figure={figures[0]} typically={typically} />
            ) : (
                <Legend
                    figures={figures}
                    picked={picked}
                    strengthOf={strengthOf}
                    light={light}
                    toggle={toggle}
                />
            )}
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
                        {guide !== null && <Guide spot={guide} box={box} />}
                        {typicalPath !== null && (
                            <Typical path={typicalPath.path} stroke={typicalPath.stroke} />
                        )}
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
