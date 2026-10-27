import clsx from 'clsx';
import { tintOf } from '@/lib/lines';
import { kindOf } from '@/components/saved/kinds';
import { UNTINTED } from '@/components/layout/tints';
import type { SavedPlace } from '@/types/place';

const PILL =
    'inline-flex shrink-0 items-center justify-center gap-1 rounded-place border text-clock font-semibold whitespace-nowrap transition-opacity duration-220 ease-out starting:opacity-0 motion-reduce:transition-none';

// Sizes for the box
const SIZES = {
    box: 'h-6 pr-1.75 pl-1.5 pointer-coarse:w-6 pointer-coarse:px-0',
    sent: 'h-5.5 pr-1.75 pl-1.5',
};

interface PlacePillProps {
    place: SavedPlace;
    size: keyof typeof SIZES;
}

// A saved place a question uses
function PlacePill({ place, size }: PlacePillProps) {
    const kind = kindOf(place.label);
    const tint = place.route_id === null ? null : tintOf(place.route_id);

    return (
        <span
            title={place.label}
            className={clsx(PILL, SIZES[size], tint === null ? UNTINTED : tint.tile)}
        >
            <kind.Icon size={12} strokeWidth={2} aria-hidden />
            <span className={clsx(size === 'box' && 'pointer-coarse:sr-only')}>{place.label}</span>
        </span>
    );
}

export default PlacePill;
