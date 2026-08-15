import clsx from 'clsx';
import { clock, segmentsOf } from '@/lib/trip';
import type { TripCard } from '@/types/answer';

interface LegBarProps {
    card: TripCard;
}

function LegBar({ card }: LegBarProps) {
    return (
        <>
            <div className="flex h-2 gap-0.5">
                {segmentsOf(card).map((segment, index) => (
                    <span
                        key={index}
                        className={clsx('rounded-full', segment.fill)}
                        style={{ width: `${segment.share}%` }}
                    />
                ))}
            </div>
            <div className="relative h-2.5 font-mono text-axis text-dim tabular-nums">
                <span className="absolute left-0">{clock(card.depart)}</span>
                <span className="absolute right-0 text-cream">{clock(card.arrive)}</span>
            </div>
        </>
    );
}

export default LegBar;
