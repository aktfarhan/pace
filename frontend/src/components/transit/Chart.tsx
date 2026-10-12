import Axis from './Axis';
import Ends from './Ends';
import Wash from './Wash';
import Paths from './Paths';
import Focus from './Focus';
import Guide from './Guide';
import Sweep from './Sweep';
import Labels from './Labels';
import Legend from './Legend';
import Heading from './Heading';
import Typical from './Typical';
import { stretchedOf } from './plot';
import { usePlot } from '@/hooks/usePlot';
import { useMemo, useState } from 'react';
import { useChartBox } from '@/hooks/useChartBox';
import type { Drawn } from '@/lib/lines';
import type { Branching, Transit } from '@/types/transit';

interface ChartProps {
    lines: readonly Drawn[];
    series: Transit['series'];
    typical: Transit['typical'];
    read: number;
    late: number;
    rolling: number;
    branching: Branching | null;
}

function Chart({ lines, series, typical, read, late, rolling, branching }: ChartProps) {
    const { cardRef, width, box, height, tight } = useChartBox();
    const [span, setSpan] = useState<number | null>(null);

    const plot = usePlot({ lines, series, typical, read, rolling, span, box });
    const { start, end } = plot.frame;
    const { follow, lift, clear } = plot.hover;
    const { picked, lead, strengthOf, toggle, light } = plot.emphasis;
    const { drawn, shown, labels, guide, figures, typically, usual, readout, wash } = plot;

    const stretched = useMemo(() => stretchedOf(drawn, rolling), [drawn, rolling]);

    return (
        <div
            ref={cardRef}
            className="flex flex-col gap-3 rounded-tile border border-seam bg-panel px-6 pt-5 pb-4"
        >
            <Heading
                late={late}
                stretched={stretched}
                tight={tight}
                span={span}
                readout={readout}
                select={setSpan}
                branching={branching}
            />
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
                        viewBox={`0 0 ${width} ${height}`}
                        className="block w-full touch-pan-y overflow-visible"
                        onPointerMove={follow}
                        onPointerUp={lift}
                        onPointerLeave={clear}
                        onPointerCancel={clear}
                    >
                        <Axis box={box} start={start} end={end} />
                        <Sweep shown={shown} left={box.left} width={width} height={height}>
                            {wash !== null && <Wash path={wash.under} text={wash.line.text} />}
                            {guide !== null && <Guide spot={guide} box={box} />}
                            {usual !== null && <Typical path={usual.path} stroke={usual.stroke} />}
                            <Paths drawn={drawn} lead={lead} strengthOf={strengthOf} />
                            <Ends drawn={drawn} end={end} strengthOf={strengthOf} />
                        </Sweep>
                        <Labels labels={labels} box={box} tight={tight} strengthOf={strengthOf} />
                    </svg>
                )}
            </div>
        </div>
    );
}

export default Chart;
