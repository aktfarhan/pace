import Dot from './Dot';
import { BUCKET_MS } from './plot';
import type { Spot } from './plot';
import type { Drawn } from '@/lib/lines';
import type { Emphasis } from '@/hooks/useEmphasis';

// How old a last reading may be and still count as now
const FRESH_MS = 3 * BUCKET_MS;

interface EndsProps {
    drawn: { line: Drawn; spots: (Spot | null)[] }[];
    end: number;
    strengthOf: Emphasis['strengthOf'];
}

function Ends({ drawn, end, strengthOf }: EndsProps) {
    // A line that stopped reporting a while ago ends with no dot
    const ends = drawn
        .map((one) => {
            const spot = one.spots.findLast((seen) => seen !== null);
            const stale = spot === undefined || end - spot.at > FRESH_MS;
            return stale ? null : { id: one.line.id, stroke: one.line.stroke, spot };
        })
        .filter((one) => one !== null);

    return (
        <>
            {ends.map((one) => (
                <g
                    key={one.id}
                    style={{ opacity: strengthOf(one.id) }}
                    className="transition-opacity ease-out"
                >
                    <Dot spot={one.spot} stroke={one.stroke} />
                </g>
            ))}
        </>
    );
}

export default Ends;
