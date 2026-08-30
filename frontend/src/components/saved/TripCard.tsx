import { X } from 'lucide-react';
import { useState } from 'react';
import Risk from '@/components/ask/cards/Risk';
import type { Planned } from '@/types/trip';

const REMOVE =
    'shrink-0 cursor-pointer text-ghost opacity-0 transition-opacity pointer-events-none hover:text-cream group-hover:pointer-events-auto group-hover:opacity-100 focus:opacity-100';

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
        <div className="group flex flex-col gap-3.5 rounded-card border border-edge bg-field px-5.5 py-5">
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
            <div className="flex items-center gap-2">
                <Risk risk={null} />
            </div>
        </div>
    );
}

export default TripCard;
