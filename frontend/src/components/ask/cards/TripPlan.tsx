import Stamp from './Stamp';
import LegBar from './LegBar';
import Timeline from './Timeline';
import { fullClock, leaveOf } from '@/lib/trip';
import type { TripCard } from '@/types/answer';

interface TripPlanProps {
    card: TripCard;
}

function TripPlan({ card }: TripPlanProps) {
    const leave = leaveOf(card, Date.now());

    return (
        <div className="flex flex-col gap-3.5 rounded-card border border-edge bg-field px-7 pt-6.5 pb-5 text-cream">
            <div className="flex items-center justify-between gap-4">
                <div className="truncate text-title text-bright">
                    {card.origin} <span className="font-medium text-hush">to</span>{' '}
                    {card.destination}
                </div>
                <Stamp card={card} />
            </div>

            <div>
                <div className="text-eyebrow text-ghost">{leave.label}</div>
                <div className="mt-1 text-depart text-accent tabular-nums text-shadow-halo">
                    {leave.time}
                    {leave.unit !== null && (
                        <span className="ml-1.75 text-depart-unit text-soft">{leave.unit}</span>
                    )}
                </div>

                <div className="mt-3 flex flex-col gap-1.75">
                    <LegBar card={card} />
                    <div className="flex items-center gap-2 pt-0.75">
                        <span className="rounded-full border border-line px-2.25 py-hair font-mono text-tag text-dim uppercase">
                            Risk —
                        </span>
                        <span className="flex-1" />
                        {leave.kind === 'none' && (
                            <>
                                <span className="font-mono text-meta text-dim uppercase tabular-nums">
                                    Next trip{' '}
                                    <span className="text-meta-value text-cream">
                                        {fullClock(card.depart)}
                                    </span>
                                </span>
                                <span className="text-edge">·</span>
                            </>
                        )}
                        <span className="font-mono text-meta text-dim uppercase tabular-nums">
                            Arrive{' '}
                            <span className="text-meta-value text-cream">
                                {fullClock(card.arrive)}
                            </span>
                        </span>
                        <span className="text-edge">·</span>
                        <span className="font-mono text-meta text-dim uppercase tabular-nums">
                            Transfers{' '}
                            <span className="text-meta-value text-cream">{card.transfers}</span>
                        </span>
                    </div>
                </div>
            </div>

            <Timeline card={card} />
        </div>
    );
}

export default TripPlan;
