import { leaveOf } from '@/lib/trip';
import { useNow } from '@/hooks/useNow';
import type { TripCard } from '@/types/answer';

interface LeaveProps {
    card: TripCard;
}

function Leave({ card }: LeaveProps) {
    const now = useNow();

    const leave = leaveOf(card, now === 0 ? Date.now() : now);

    return (
        <>
            <div className="text-eyebrow text-ghost">{leave.label}</div>
            <div className="mt-1 text-depart text-accent tabular-nums text-shadow-halo">
                {leave.time}
                {leave.unit !== null && (
                    <span className="ml-1.75 text-depart-unit text-soft">{leave.unit}</span>
                )}
            </div>
        </>
    );
}

export default Leave;
