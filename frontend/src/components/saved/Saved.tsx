import Refresh from './Refresh';
import AddPlace from './AddPlace';
import TripCard from './TripCard';
import PlaceCard from './PlaceCard';
import { POLL_MS } from '@/lib/poll';
import { useTrips } from '@/hooks/useTrips';
import { usePlaces } from '@/hooks/usePlaces';
import Empty from '@/components/layout/Empty';
import Failed from '@/components/layout/Failed';
import { MessageSquare, Route } from 'lucide-react';
import SectionHeading from '@/components/layout/SectionHeading';

interface SavedProps {
    start: () => void;
}

function Saved({ start }: SavedProps) {
    const { places, failed: placesFailed, retry, keep, drop: dropPlace } = usePlaces();
    const { trips, readAt, reading, failed: tripsFailed, refresh, drop: dropTrip } = useTrips();

    return (
        <div className="flex flex-col gap-3.5">
            <div className="flex items-center justify-between gap-4">
                <span className="text-board text-bright">Saved</span>
                {trips !== null && trips.length > 0 && (
                    <Refresh readAt={readAt} reading={reading} refresh={refresh} />
                )}
            </div>

            <div>
                <SectionHeading label="Places" />
                {placesFailed && (
                    <Failed said="Couldn't reach your places" retry={retry} className="px-1 pb-3" />
                )}

                <div className="grid grid-cols-4 gap-3">
                    {places?.map((place) => (
                        <PlaceCard key={place.id} place={place} drop={dropPlace} />
                    ))}
                    <AddPlace keep={keep} />
                </div>
            </div>

            <div>
                <SectionHeading label="Trips" />
                {trips === null && !tripsFailed && (
                    <p className="px-1 text-row text-faint">Reading your trips…</p>
                )}
                {trips === null && tripsFailed && (
                    <Failed
                        said="Couldn't reach your trips"
                        retry={refresh}
                        className="px-1 pb-3"
                    />
                )}
                {trips !== null && trips.length === 0 && (
                    <Empty
                        Icon={Route}
                        title="Trips you save show up here"
                        note={`Bookmark any trip and its next departures stay here, re-planned every ${POLL_MS / 1000} seconds.`}
                        action="Plan a trip"
                        ActionIcon={MessageSquare}
                        run={start}
                    />
                )}

                {trips !== null && (
                    <div className="grid grid-cols-2 items-start gap-3">
                        {trips.map((trip) => (
                            <TripCard key={trip.id} trip={trip} drop={dropTrip} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Saved;
