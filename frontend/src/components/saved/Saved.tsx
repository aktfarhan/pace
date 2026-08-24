import PlaceCard from './PlaceCard';
import { usePlaces } from '@/hooks/usePlaces';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';

function Saved() {
    const places = usePlaces();

    let body = null;

    if (places !== null && places.length === 0) {
        body = <p className="px-0.5 text-row text-dim">No places saved.</p>;
    }

    if (places !== null && places.length > 0) {
        body = (
            <div className="grid grid-cols-4 gap-3">
                {places.map((place) => (
                    <PlaceCard key={place.id} place={place} />
                ))}
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3.5">
            <span className="text-board text-bright">Saved</span>

            <div>
                <SectionHeading label="Places" />
                {body}
            </div>
        </div>
    );
}

export default Saved;
