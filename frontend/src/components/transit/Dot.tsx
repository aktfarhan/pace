import type { Spot } from './plot';

interface DotProps {
    spot: Spot;
    stroke: string;
}

function Dot({ spot, stroke }: DotProps) {
    return (
        <>
            <circle cx={spot.x} cy={spot.y} r={6} className="fill-panel" />
            <circle cx={spot.x} cy={spot.y} r={1.75} strokeWidth={3.5} className={stroke} />
        </>
    );
}

export default Dot;
