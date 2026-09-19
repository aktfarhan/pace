import type { Box, Label } from './plot';

const ROOM = 62;

interface LabelsProps {
    labels: Label[];
    box: Box;
    tight: boolean;
}

// A dot on every line with its share beside it
function Labels({ labels, box, tight }: LabelsProps) {
    // Near the right edge the readout swaps sides
    const flip = labels.length > 0 && labels[0].spot.x > box.right - ROOM;

    return (
        <g>
            {labels.map((label) => (
                <g key={label.id}>
                    <circle
                        cx={label.spot.x}
                        cy={label.spot.y}
                        r={3.25}
                        strokeWidth={2}
                        className={`${label.stroke} fill-panel`}
                    />
                    <text
                        x={label.spot.x + (flip ? -8 : 8)}
                        y={label.y}
                        textAnchor={flip ? 'end' : 'start'}
                        className={`${label.mark} font-mono text-axis font-strong`}
                    >
                        {!tight && `${label.code} `}
                        {label.spot.share}%
                    </text>
                </g>
            ))}
        </g>
    );
}

export default Labels;
