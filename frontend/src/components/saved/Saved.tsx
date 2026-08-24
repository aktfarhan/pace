import AddPlace from './AddPlace';
import PlaceCard from './PlaceCard';
import { usePlaces } from '@/hooks/usePlaces';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';

function Saved() {
    const { places, keep } = usePlaces();

    return (
        <div className="flex flex-col gap-3.5">
            <span className="text-board text-bright">Saved</span>

            <div>
                <SectionHeading label="Places" />

                {places !== null && (
                    <div className="grid grid-cols-4 gap-3">
                        {places.map((place) => (
                            <PlaceCard key={place.id} place={place} />
                        ))}
                        <AddPlace keep={keep} />
                    </div>
                )}
            </div>
        </div>
    );
}

export default Saved;
