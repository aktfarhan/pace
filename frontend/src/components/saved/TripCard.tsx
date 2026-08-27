import Risk from '@/components/ask/cards/Risk';
import type { SavedTrip } from '@/types/trip';

interface TripCardProps {
    trip: SavedTrip;
}

function TripCard({ trip }: TripCardProps) {
    return (
        <div className="flex flex-col gap-3.5 rounded-card border border-edge bg-field px-5.5 py-5">
            <div className="truncate text-title text-bright">
                {trip.origin} <span className="font-medium text-hush">to</span> {trip.destination}
            </div>
            <div className="flex items-center gap-2">
                <Risk risk={null} />
            </div>
        </div>
    );
}

export default TripCard;
