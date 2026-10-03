import clsx from 'clsx';
import { ageOf } from '@/lib/status';
import { useNow } from '@/hooks/useNow';
import type { TripCard } from '@/types/answer';

// How long a live reading keeps pulsing
const FRESH_MS = 120000;

interface StampProps {
    card: TripCard;
}

function Stamp({ card }: StampProps) {
    const now = useNow();
    const fresh = now - Date.parse(card.retrieved_at) < FRESH_MS;

    return (
        <span className="flex shrink-0 items-center gap-2 font-mono text-stamp uppercase">
            {card.live && (
                <span
                    className={clsx('size-1.25 rounded-full bg-accent', fresh && 'animate-pace')}
                />
            )}
            {card.live ? 'Live' : 'Scheduled'} · {ageOf(card.retrieved_at, now)}
        </span>
    );
}

export default Stamp;
