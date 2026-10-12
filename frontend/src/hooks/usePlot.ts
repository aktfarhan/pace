import { useMemo } from 'react';
import { useHover } from './useHover';
import { useEmphasis } from './useEmphasis';
import { windowOf } from '@/components/transit/frame';
import { figuresOf, readoutOf, typicalOf } from '@/components/transit/figures';
import { marksOf, nearestOf, seriesOf, stackOf } from '@/components/transit/plot';
import type { Drawn } from '@/lib/lines';
import type { Transit } from '@/types/transit';
import type { Box } from '@/components/transit/plot';

interface PlotInput {
    lines: readonly Drawn[];
    series: Transit['series'];
    typical: Transit['typical'];
    read: number;
    rolling: number;
    span: number | null;
    box: Box;
}

// Everything the chart draws and reads back
export function usePlot({ lines, series, typical, read, rolling, span, box }: PlotInput) {
    // Where the chart starts and ends for the picked span
    const { start, end } = useMemo(() => {
        const days = lines.map((line) => series[line.id]);
        return windowOf(read, days, span);
    }, [lines, read, series, span]);

    // Each line's readings placed on the chart
    const drawn = useMemo(
        () => lines.map((line) => ({ line, ...seriesOf(series[line.id], start, end, box) })),
        [lines, series, start, end, box],
    );

    // The lines the hover reads from
    const shown = drawn.map((one) => one.line.id).join();
    const sheets = useMemo(() => drawn.map((one) => one.spots), [drawn]);
    const { held, reading, follow, lift, clear } = useHover(sheets, shown, start, end, box);

    const marks = marksOf(drawn, reading);
    const near = held === null ? null : nearestOf(marks, held.y);
    const emphasis = useEmphasis(shown, near);

    const figures = useMemo(() => figuresOf(lines, series), [lines, series]);
    const typically = useMemo(() => typicalOf(typical, lines), [typical, lines]);

    // The typical line, under a line drawn alone
    const usual = useMemo(() => {
        if (lines.length !== 1) return null;

        const { path, spots } = seriesOf(typical[lines[0].id], start, end, box);
        return path === '' ? null : { path, stroke: lines[0].stroke, spots };
    }, [lines, typical, start, end, box]);

    // The typical share at the hovered quarter
    const usually = reading === null ? null : (usual?.spots[reading]?.share ?? null);

    return {
        frame: { start, end },
        hover: { follow, lift, clear },
        emphasis,
        drawn,
        shown,
        labels: stackOf(marks, box.floor),
        guide: marks.length === 0 ? null : marks[0].spot,
        figures,
        typically,
        usual,
        readout: readoutOf(marks, usually, rolling, lines.length === 1),
        wash: drawn.length === 1 && drawn[0].under !== '' ? drawn[0] : null,
    };
}
