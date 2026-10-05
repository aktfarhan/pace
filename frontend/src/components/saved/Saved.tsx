import { useRef } from 'react';
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
    const titleRef = useRef<HTMLHeadingElement>(null);
    const { places, failed: placesFailed, retry, keep, drop: dropPlace } = usePlaces();
    const { trips, readAt, reading, failed: tripsFailed, refresh, drop: dropTrip } = useTrips();

    return (
        <div className="@container flex flex-col gap-3.5">
            <div className="flex items-center justify-between gap-4">
                <h1 ref={titleRef} tabIndex={-1} className="text-board text-bright">
                    Saved
                </h1>
                {trips !== null && trips.length > 0 && (
                    <Refresh readAt={readAt} reading={reading} refresh={refresh} />
                )}
            </div>

            <div>
                <SectionHeading label="Places" count={places?.length} />
                {placesFailed && (
                    <Failed said="Couldn't reach your places" retry={retry} className="px-1 pb-3" />
                )}

                <div className="grid grid-cols-1 gap-3 @md:grid-cols-2 @2xl:grid-cols-3 @4xl:grid-cols-4">
                    {places?.map((place) => (
                        <PlaceCard
                            key={place.id}
                            place={place}
                            drop={dropPlace}
                            titleRef={titleRef}
                        />
                    ))}
                    <AddPlace keep={keep} first={places !== null && places.length === 0} />
                </div>
            </div>

            <div>
                <SectionHeading label="Trips" count={trips?.length} />
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
                    <div className="grid grid-cols-1 items-start gap-3 @3xl:grid-cols-2">
                        {trips.map((trip) => (
                            <TripCard
                                key={trip.id}
                                trip={trip}
                                drop={dropTrip}
                                titleRef={titleRef}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Saved;
