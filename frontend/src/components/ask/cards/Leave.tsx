import clsx from 'clsx';
import { leaveOf } from '@/lib/trip';
import { useNow } from '@/hooks/useNow';
import { useTicks } from '@/hooks/useTicks';
import { TICK } from '@/components/layout/tints';
import type { TripCard } from '@/types/answer';

interface LeaveProps {
    card: TripCard;
}

function Leave({ card }: LeaveProps) {
    const now = useNow();
    const leave = leaveOf(card, now);

    const { ticking, settle } = useTicks([
        ['label', leave.label],
        ['time', leave.time],
    ]);

    return (
        <>
            <div
                key={leave.label}
                onTransitionEnd={() => settle('label', leave.label)}
                className={clsx('text-eyebrow text-dim', ticking('label', leave.label) && TICK)}
            >
                {leave.label}
            </div>
            <div
                key={leave.time}
                onTransitionEnd={() => settle('time', leave.time)}
                className={clsx(
                    'mt-1 text-depart text-accent tabular-nums text-shadow-halo',
                    ticking('time', leave.time) && TICK,
                )}
            >
                {leave.time}
                {leave.unit !== null && (
                    <span className="ml-1.75 text-depart-unit text-soft">{leave.unit}</span>
                )}
            </div>
        </>
    );
}

export default Leave;
