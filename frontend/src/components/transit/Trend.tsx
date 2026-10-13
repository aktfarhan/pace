import { BUCKET_MS } from './plot';
import { curveMonotoneX, line } from 'd3-shape';
import type { Standing } from '@/types/transit';

// The sparkline's size and its share floor
const WIDTH = 44;
const HEIGHT = 18;
const FLOOR_SHARE = 20;

// One reading of the day so far
type Point = Standing['trend'][number];

interface TrendProps {
    points: Point[];
}

function Trend({ points }: TrendProps) {
    if (points.length < 2) return null;

    const first = points[0].at;
    const span = points[points.length - 1].at - first;
    const top = Math.max(...points.map((point) => point.share), FLOOR_SHARE);

    // A null between far-apart readings leaves a gap
    const spaced: (Point | null)[] = [];
    points.forEach((point, index) => {
        if (index > 0 && point.at - points[index - 1].at > BUCKET_MS) spaced.push(null);
        spaced.push(point);
    });

    // The day's line
    const path = line<Point | null>()
        .defined((point) => point !== null)
        .x((point) => (point === null ? 0 : ((point.at - first) / span) * WIDTH))
        .y((point) => (point === null ? 0 : HEIGHT - 1 - (point.share / top) * (HEIGHT - 2)))
        .curve(curveMonotoneX)(spaced);

    return (
        <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            preserveAspectRatio="none"
            aria-hidden="true"
            className="block h-4.5 w-full overflow-visible"
        >
            <path
                d={path ?? ''}
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
            />
        </svg>
    );
}

export default Trend;
