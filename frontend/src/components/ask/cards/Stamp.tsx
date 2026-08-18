import { ageOf } from '@/lib/status';
import { useNow } from '@/hooks/useNow';
import type { TripCard } from '@/types/answer';

interface StampProps {
    card: TripCard;
}

function Stamp({ card }: StampProps) {
    const now = useNow();

    return (
        <span className="flex shrink-0 items-center gap-2 font-mono text-stamp uppercase">
            {card.live && <span className="size-1.25 animate-pace rounded-full bg-accent" />}
            {card.live ? 'Live' : 'Scheduled'} · {ageOf(card.retrieved_at, now)}
        </span>
    );
}

export default Stamp;
