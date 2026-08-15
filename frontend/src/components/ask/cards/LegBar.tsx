import clsx from 'clsx';
import { LINE_FILLS, clock, lineOf } from '@/lib/trip';
import type { TripCard } from '@/types/answer';

interface LegBarProps {
    card: TripCard;
}

function LegBar({ card }: LegBarProps) {
    const total = Date.parse(card.arrive) - Date.parse(card.depart);

    return (
        <>
            <div className="flex h-2 gap-0.5">
                {card.legs.map((leg, index) => {
                    const line = leg.kind === 'ride' ? lineOf(leg.route_id) : null;
                    const span = Date.parse(leg.arrive) - Date.parse(leg.depart);
                    const share = (span / total) * 100;
                    return (
                        <span
                            key={index}
                            className={clsx(
                                'rounded-full',
                                line === null ? 'bg-quiet' : LINE_FILLS[line],
                            )}
                            style={{ width: `${share}%` }}
                        />
                    );
                })}
            </div>
            <div className="relative h-2.5 font-mono text-axis text-dim tabular-nums">
                <span className="absolute left-0">{clock(card.depart)}</span>
                <span className="absolute right-0 text-cream">{clock(card.arrive)}</span>
            </div>
        </>
    );
}

export default LegBar;
