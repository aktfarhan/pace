import Risk from './Risk';
import Leave from './Leave';
import Stamp from './Stamp';
import LegBar from './LegBar';
import Timeline from './Timeline';
import { RotateCw } from 'lucide-react';
import { fullClock, leaveOf } from '@/lib/trip';
import type { Level, TripCard } from '@/types/answer';

interface TripPlanProps {
    card: TripCard;
    risk: Level | null;
    refresh: () => void;
    refreshing: boolean;
}

function TripPlan({ card, risk, refresh, refreshing }: TripPlanProps) {
    const leave = leaveOf(card, Date.now());

    return (
        <div className="flex flex-col gap-3.5 rounded-card border border-edge bg-field px-7 pt-6.5 pb-5 text-cream">
            <div className="flex items-center justify-between gap-4">
                <div className="truncate text-title text-bright">
                    {card.origin} <span className="font-medium text-hush">to</span>{' '}
                    {card.destination}
                </div>
                <button
                    type="button"
                    onClick={refresh}
                    title="Refresh this plan"
                    className="flex shrink-0 cursor-pointer items-center gap-2 rounded-full border border-edge bg-bubble px-3.25 py-1.75 text-hush transition-colors hover:border-ghost hover:bg-line hover:text-cream"
                >
                    <Stamp card={card} />
                    <RotateCw
                        size={12}
                        strokeWidth={2.4}
                        className={refreshing ? 'animate-spin text-quiet' : 'text-quiet'}
                        aria-hidden="true"
                    />
                </button>
            </div>
            <div>
                <Leave card={card} />
                <div className="mt-3 flex flex-col gap-1.75">
                    <LegBar card={card} />
                    <div className="flex items-center gap-2 pt-0.75">
                        <Risk risk={risk} />
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
