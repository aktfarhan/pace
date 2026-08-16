import LegRow from './LegRow';
import { MapPin } from 'lucide-react';
import { clock, timelineOf } from '@/lib/trip';
import type { TripCard } from '@/types/answer';

interface TimelineProps {
    card: TripCard;
}

function Timeline({ card }: TimelineProps) {
    return (
        <div className="border-t border-seam">
            {timelineOf(card).map((leg, index) => (
                <LegRow key={index} leg={leg} bright={index === 0} />
            ))}

            <div className="flex items-center gap-3 border-t border-seam px-0.5 py-2.75">
                <span className="w-11 shrink-0 font-mono text-clock font-strong text-accent tabular-nums">
                    {clock(card.arrive)}
                </span>
                <span className="grid size-7 shrink-0 place-items-center rounded-mark border border-good/30 bg-good/12 text-green">
                    <MapPin size={14} strokeWidth={1.9} aria-hidden="true" />
                </span>
                <span className="min-w-0 flex-1 truncate text-row font-semibold text-cream">
                    Arrive · {card.destination}
                </span>
                <span className="w-19 shrink-0 text-right font-mono text-tag text-green uppercase">
                    Arrive
                </span>
            </div>
        </div>
    );
}

export default Timeline;
