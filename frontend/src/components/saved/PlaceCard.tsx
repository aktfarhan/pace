import clsx from 'clsx';
import { useState } from 'react';
import { LINE_CHIPS, lineOf } from '@/lib/trip';
import { Briefcase, House, MapPin, X } from 'lucide-react';
import type { SavedPlace } from '@/types/place';

const CHIP = 'rounded-chip border px-2 py-0.75 font-mono text-chip whitespace-nowrap uppercase';

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

    const line = place.route_id === null ? null : lineOf(place.route_id);
    const walk = place.walk_seconds === null ? 0 : Math.ceil(place.walk_seconds / 60);

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

            {place.station === null ? (
                <span className={`${CHIP} w-fit border-dashed border-line bg-ink text-ghost`}>
                    Station —
                </span>
            ) : (
                <div className="flex items-center gap-1.75">
                    <span
                        className={clsx(
                            CHIP,
                            'min-w-0 truncate',
                            line === null ? 'border-line bg-bubble text-muted' : LINE_CHIPS[line],
                        )}
                    >
                        {place.station}
                    </span>
                    {walk > 0 && (
                        <span className="shrink-0 font-mono text-toward whitespace-nowrap text-faint uppercase">
                            {walk} min walk
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}

export default PlaceCard;
