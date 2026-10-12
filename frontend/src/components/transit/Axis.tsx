import { DROP } from './plot';
import { memo, useMemo } from 'react';
import { rulesOf, ticksOf } from './frame';
import type { Box } from './plot';

// How far the hour labels sit below the floor
const LABEL = 22;

// How far the share labels sit left of the plot
const SHARE = 10;

// How far a share label drops to sit on its rule
const BASELINE = 3.5;

interface AxisProps {
    box: Box;
    start: number;
    end: number;
}

function Axis({ box, start, end }: AxisProps) {
    const rules = useMemo(() => rulesOf(box), [box]);
    const ticks = useMemo(() => ticksOf(start, end, box), [start, end, box]);

    return (
        <g>
            {rules.map((rule) => (
                <g key={rule.share}>
                    {rule.share > 0 && (
                        <line
                            x1={box.left}
                            y1={rule.y}
                            x2={box.right}
                            y2={rule.y}
                            className="stroke-rule"
                            strokeWidth={1}
                        />
                    )}
                    {rule.label !== null && (
                        <text
                            x={box.left - SHARE}
                            y={rule.y + BASELINE}
                            textAnchor="end"
                            className="fill-ghost font-mono text-axis"
                        >
                            {rule.label}
                        </text>
                    )}
                </g>
            ))}

            <line
                x1={box.left}
                y1={box.floor + DROP}
                x2={box.right}
                y2={box.floor + DROP}
                className="stroke-edge"
                strokeWidth={1}
            />

            {ticks.map((tick) => (
                <text
                    key={tick.at}
                    x={tick.x}
                    y={box.floor + LABEL}
                    textAnchor="middle"
                    className="fill-faint font-mono text-axis"
                >
                    {tick.label}
                </text>
            ))}
        </g>
    );
}

export default memo(Axis);
