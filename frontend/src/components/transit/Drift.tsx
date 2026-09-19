import clsx from 'clsx';
import { ArrowDown, ArrowUp } from 'lucide-react';

interface DriftProps {
    points: number | null;
}

function Drift({ points }: DriftProps) {
    if (points === null) return null;

    const rising = points > 0;
    const Arrow = rising ? ArrowUp : ArrowDown;

    return (
        <span
            className={clsx(
                'inline-flex shrink-0 items-center gap-1 font-mono text-label tabular-nums',
                rising ? 'text-delay' : 'text-steady',
            )}
        >
            <Arrow size={10} strokeWidth={3} aria-hidden="true" />
            {Math.abs(points)}
        </span>
    );
}

export default Drift;
