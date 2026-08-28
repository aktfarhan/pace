import AddPlace from './AddPlace';
import TripCard from './TripCard';
import PlaceCard from './PlaceCard';
import { useTrips } from '@/hooks/useTrips';
import { usePlaces } from '@/hooks/usePlaces';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';

function Saved() {
    const { places, keep, drop } = usePlaces();
    const trips = useTrips();

    return (
        <div className="flex flex-col gap-3.5">
            <span className="text-board text-bright">Saved</span>

            <div>
                <SectionHeading label="Places" />

                {places !== null && (
                    <div className="grid grid-cols-4 gap-3">
                        {places.map((place) => (
                            <PlaceCard key={place.id} place={place} drop={drop} />
                        ))}
                        <AddPlace keep={keep} />
                    </div>
                )}
            </div>

            <div>
                <SectionHeading label="Trips" />

                {trips !== null && (
                    <div className="grid grid-cols-2 gap-3">
                        {trips.map((trip) => (
                            <TripCard key={trip.id} trip={trip} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Saved;
