import { X } from 'lucide-react';
import { useState } from 'react';
import { fullClock } from '@/lib/trip';
import Risk from '@/components/ask/cards/Risk';
import Leave from '@/components/ask/cards/Leave';
import LegBar from '@/components/ask/cards/LegBar';
import Chance from '@/components/ask/cards/Chance';
import Timeline from '@/components/ask/cards/Timeline';
import type { Planned } from '@/types/trip';

const REMOVE =
    'shrink-0 cursor-pointer text-ghost opacity-0 transition-opacity pointer-events-none hover:text-cream group-hover:pointer-events-auto group-hover:opacity-100 focus:opacity-100';

const META = 'font-mono text-meta text-dim uppercase tabular-nums';

interface TripCardProps {
    trip: Planned;
    drop: (id: number) => Promise<void>;
}

function TripCard({ trip, drop }: TripCardProps) {
    const [removing, setRemoving] = useState(false);

    // Drops a trip
    const remove = async () => {
        if (removing) return;

        setRemoving(true);
        try {
            await drop(trip.id);
        } catch (error) {
            console.error(error);
            setRemoving(false);
        }
    };

    return (
        <div className="group flex flex-col gap-3.5 rounded-card border border-edge bg-field px-5.5 pt-5.5 pb-4 text-cream">
            <div className="flex items-center gap-2.5">
                <div className="min-w-0 flex-1 truncate text-title text-bright">
                    {trip.origin} <span className="font-medium text-hush">to</span>{' '}
                    {trip.destination}
                </div>
                <button
                    type="button"
                    onClick={remove}
                    disabled={removing}
                    aria-label={`Remove ${trip.origin} to ${trip.destination}`}
                    className={REMOVE}
                >
                    <X size={14} strokeWidth={2.2} aria-hidden="true" />
                </button>
            </div>

            {trip.card === null ? (
                <div className="flex items-center gap-2 pb-1">
                    <Risk risk={trip.risk} />
                </div>
            ) : (
                <>
                    <div>
                        <Leave card={trip.card} />
                        <div className="mt-3 flex flex-col gap-1.75">
                            <LegBar card={trip.card} />
                            <div className="flex items-center gap-2 pt-0.75">
                                <Risk risk={trip.risk} />
                                <Chance chance={trip.chance} />
                                <span className="flex-1" />
                                <span className={META}>
                                    Arrive{' '}
                                    <span className="text-meta-value text-cream">
                                        {fullClock(trip.card.arrive)}
                                    </span>
                                </span>
                                <span className="text-edge">·</span>
                                <span className={META}>
                                    Transfers{' '}
                                    <span className="text-meta-value text-cream">
                                        {trip.card.transfers}
                                    </span>
                                </span>
                            </div>
                        </div>
                    </div>
                    <Timeline card={trip.card} />
                </>
            )}
        </div>
    );
}

export default TripCard;
