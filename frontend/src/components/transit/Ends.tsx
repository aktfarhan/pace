import type { Spot } from './plot';
import type { Emphasis } from '@/hooks/useEmphasis';

interface End {
    id: string;
    stroke: string;
    spot: Spot;
}

interface EndsProps {
    ends: End[];
    strengthOf: Emphasis['strengthOf'];
}

function Ends({ ends, strengthOf }: EndsProps) {
    return (
        <g>
            {ends.map((end) => (
                <circle
                    key={end.id}
                    cx={end.spot.x}
                    cy={end.spot.y}
                    r={3}
                    strokeWidth={2}
                    opacity={strengthOf(end.id)}
                    className={`${end.stroke} fill-panel`}
                />
            ))}
        </g>
    );
}

export default Ends;
