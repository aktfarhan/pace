import Dot from './Dot';
import type { Box, Label } from './plot';
import type { Emphasis } from '@/hooks/useEmphasis';

const ROOM = 62;

// The least a readout dims
const FLOOR_OPACITY = 0.5;

// A label's gap from its dot
const GAP = 9;

interface LabelsProps {
    labels: Label[];
    box: Box;
    tight: boolean;
    strengthOf: Emphasis['strengthOf'];
}

// A dot on every line with its share beside it
function Labels({ labels, box, tight, strengthOf }: LabelsProps) {
    // Near the right edge the readout swaps sides
    const flip = labels.length > 0 && labels[0].spot.x > box.right - ROOM;

    return (
        <>
            {labels.map((label) => (
                <g
                    key={label.id}
                    style={{ opacity: Math.max(strengthOf(label.id), FLOOR_OPACITY) }}
                    className="transition-opacity ease-out"
                >
                    <Dot spot={label.spot} stroke={label.stroke} />
                    <text
                        x={label.spot.x + (flip ? -GAP : GAP)}
                        y={label.y}
                        textAnchor={flip ? 'end' : 'start'}
                        paintOrder="stroke"
                        strokeWidth={4}
                        strokeLinejoin="round"
                        className={`${label.mark} stroke-panel font-mono text-axis font-strong`}
                    >
                        {!tight && `${label.code} `}
                        {label.spot.share}%
                    </text>
                </g>
            ))}
        </>
    );
}

export default Labels;
