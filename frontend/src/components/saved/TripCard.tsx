import clsx from 'clsx';
import Undo from './Undo';
import { X } from 'lucide-react';
import { REMOVE } from './tints';
import Risk from '@/components/ask/cards/Risk';
import Plan from '@/components/ask/cards/Plan';
import { useRemoval } from '@/hooks/useRemoval';
import type { RefObject } from 'react';
import type { Planned } from '@/types/trip';

interface TripCardProps {
    trip: Planned;
    drop: (id: number) => Promise<void>;
    titleRef: RefObject<HTMLHeadingElement | null>;
}

function TripCard({ trip, drop, titleRef }: TripCardProps) {
    const { cardRef, removeRef, going, failed, remove, undo } = useRemoval(drop, trip.id, titleRef);

    return (
        <div
            ref={cardRef}
            className="group flex flex-col gap-3.5 rounded-card border border-edge bg-field px-5.5 pt-5.5 pb-4 text-cream"
        >
            <div className="flex h-4.25 items-center gap-2.5">
                {going ? (
                    <Undo said={`${trip.origin} to ${trip.destination} removed`} undo={undo} />
                ) : (
                    <>
                        <div className="min-w-0 flex-1 truncate text-title text-bright">
                            {trip.origin} <span className="font-medium text-hush">to</span>{' '}
                            {trip.destination}
                        </div>
                        <button
                            ref={removeRef}
                            type="button"
                            onClick={remove}
                            aria-label={`Remove ${trip.origin} to ${trip.destination}`}
                            className={REMOVE}
                        >
                            <X size={14} strokeWidth={2.2} />
                        </button>
                    </>
                )}
            </div>

            {failed && !going && (
                <span role="alert" className="-mt-1.5 text-row text-red">
                    Couldn't remove this trip. Try again.
                </span>
            )}
            <div
                className={clsx(
                    'flex flex-col gap-3.5 transition-opacity ease-out',
                    going && 'opacity-35',
                )}
            >
                {trip.card === null ? (
                    <div className="flex items-center gap-2.5 pb-1">
                        <Risk risk={trip.risk} />
                        <span className="text-row text-faint">No route right now.</span>
                    </div>
                ) : (
                    <Plan card={trip.card} risk={trip.risk} chance={trip.chance} />
                )}
            </div>
        </div>
    );
}

export default TripCard;
