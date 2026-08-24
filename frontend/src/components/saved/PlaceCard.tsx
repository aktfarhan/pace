import { Briefcase, House, MapPin } from 'lucide-react';
import type { SavedPlace } from '@/types/place';

interface PlaceCardProps {
    place: SavedPlace;
}

function PlaceCard({ place }: PlaceCardProps) {
    const named = place.label.trim().toLowerCase();

    let Icon = MapPin;
    if (named === 'home') Icon = House;
    if (named === 'work') Icon = Briefcase;

    return (
        <div className="flex flex-col gap-2.75 rounded-tile border border-seam bg-panel px-4.25 py-4">
            <div className="flex items-center gap-2.5">
                <span className="grid size-7 shrink-0 place-items-center rounded-mark border border-line bg-bubble">
                    <Icon size={14} strokeWidth={1.9} className="text-muted" aria-hidden="true" />
                </span>
                <span className="min-w-0 flex-1 truncate text-base font-strong text-bright">
                    {place.label}
                </span>
            </div>

            <span className="truncate text-row text-hush">{place.address}</span>

            <span className="w-fit rounded-chip border border-dashed border-line bg-ink px-2 py-0.75 font-mono text-chip whitespace-nowrap text-ghost uppercase">
                Station —
            </span>
        </div>
    );
}

export default PlaceCard;
