import { useState } from 'react';
import { Briefcase, House, MapPin, X } from 'lucide-react';
import type { SavedPlace } from '@/types/place';

const REMOVE =
    'shrink-0 cursor-pointer text-ghost opacity-0 transition-opacity pointer-events-none hover:text-cream group-hover:pointer-events-auto group-hover:opacity-100 focus:opacity-100';

interface PlaceCardProps {
    place: SavedPlace;
    drop: (id: number) => Promise<void>;
}

function PlaceCard({ place, drop }: PlaceCardProps) {
    const [removing, setRemoving] = useState(false);

    const named = place.label.trim().toLowerCase();

    let Icon = MapPin;
    if (named === 'home') Icon = House;
    if (named === 'work') Icon = Briefcase;

    // Drops a place
    const remove = async () => {
        if (removing) return;

        setRemoving(true);
        try {
            await drop(place.id);
        } catch (error) {
            console.error(error);
            setRemoving(false);
        }
    };

    return (
        <div className="group flex flex-col gap-2.75 rounded-tile border border-seam bg-panel px-4.25 py-4">
            <div className="flex items-center gap-2.5">
                <span className="grid size-7 shrink-0 place-items-center rounded-mark border border-line bg-bubble">
                    <Icon size={14} strokeWidth={1.9} className="text-muted" aria-hidden="true" />
                </span>
                <span className="min-w-0 flex-1 truncate text-base font-strong text-bright">
                    {place.label}
                </span>
                <button
                    type="button"
                    onClick={remove}
                    disabled={removing}
                    aria-label={`Remove ${place.label}`}
                    className={REMOVE}
                >
                    <X size={14} strokeWidth={2.2} aria-hidden="true" />
                </button>
            </div>

            <span className="truncate text-row text-hush">{place.address}</span>

            <span className="w-fit rounded-chip border border-dashed border-line bg-ink px-2 py-0.75 font-mono text-chip whitespace-nowrap text-ghost uppercase">
                Station —
            </span>
        </div>
    );
}

export default PlaceCard;
