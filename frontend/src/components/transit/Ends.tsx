import type { Spot } from './plot';

interface End {
    id: string;
    stroke: string;
    spot: Spot;
}

interface EndsProps {
    ends: End[];
}

function Ends({ ends }: EndsProps) {
    return (
        <g>
            {ends.map((end) => (
                <circle
                    key={end.id}
                    cx={end.spot.x}
                    cy={end.spot.y}
                    r={3}
                    strokeWidth={2}
                    className={`${end.stroke} fill-panel`}
                />
            ))}
        </g>
    );
}

export default Ends;
