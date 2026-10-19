import clsx from 'clsx';
import { ArrowDown, ArrowUp } from 'lucide-react';

interface DriftProps {
    points: number | null;
}

function Drift({ points }: DriftProps) {
    if (points === null) return null;

    const rising = points > 0;
    const Arrow = rising ? ArrowUp : ArrowDown;
    const said = `${rising ? 'Up' : 'Down'} ${Math.abs(points)} points in the last hour`;

    return (
        <span
            title={said}
            className={clsx(
                'inline-flex shrink-0 items-center gap-1 font-mono text-label tabular-nums',
                rising ? 'text-delay' : 'text-steady',
            )}
        >
            <Arrow size={10} strokeWidth={3} />
            <span aria-hidden="true">{Math.abs(points)}</span>
            <span className="sr-only">{said}</span>
        </span>
    );
}

export default Drift;
