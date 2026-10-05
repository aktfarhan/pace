import clsx from 'clsx';
import Undo from './Undo';
import { kindOf } from './kinds';
import { REMOVE } from './tints';
import { tintOf } from '@/lib/lines';
import { MapPinOff, X } from 'lucide-react';
import { useRemoval } from '@/hooks/useRemoval';
import { UNTINTED } from '@/components/layout/tints';
import type { RefObject } from 'react';
import type { SavedPlace } from '@/types/place';

const CHIP = 'rounded-chip border px-2 py-0.75 font-mono text-chip whitespace-nowrap uppercase';

interface PlaceCardProps {
    place: SavedPlace;
    drop: (id: number) => Promise<void>;
    titleRef: RefObject<HTMLHeadingElement | null>;
}

function PlaceCard({ place, drop, titleRef }: PlaceCardProps) {
    const { cardRef, removeRef, going, failed, remove, undo } = useRemoval(
        drop,
        place.id,
        titleRef,
    );

    const kind = kindOf(place.label);

    const tint = place.route_id === null ? null : tintOf(place.route_id);
    const walk = place.walk_seconds === null ? 0 : Math.ceil(place.walk_seconds / 60);

    return (
        <div
            ref={cardRef}
            className="group flex flex-col gap-2.75 rounded-tile border border-seam bg-panel px-4.25 py-4"
        >
            <div className="flex h-7 items-center gap-2.5">
                {going ? (
                    <Undo said={`${place.label} removed`} undo={undo} />
                ) : (
                    <>
                        <span
                            className={clsx(
                                'grid size-7 shrink-0 place-items-center rounded-mark border',
                                tint === null ? UNTINTED : tint.tile,
                            )}
                        >
                            <kind.Icon size={14} strokeWidth={1.9} />
                        </span>
                        <span className="min-w-0 flex-1 truncate text-title text-bright">
                            {place.label}
                        </span>
                        <button
                            ref={removeRef}
                            type="button"
                            onClick={remove}
                            aria-label={`Remove ${place.label}`}
                            className={REMOVE}
                        >
                            <X size={14} strokeWidth={2.2} />
                        </button>
                    </>
                )}
            </div>
            <div
                className={clsx(
                    'flex flex-col gap-2.75 transition-opacity ease-out',
                    going && 'opacity-35',
                )}
            >
                <span className="truncate text-row text-hush">{place.address}</span>
                {failed && !going && (
                    <span role="alert" className="text-row text-red">
                        Couldn't remove this place. Try again.
                    </span>
                )}

                {place.station === null ? (
                    <span className="flex items-center gap-1.5 text-row text-faint">
                        <MapPinOff size={13} strokeWidth={2} />
                        No nearby station
                    </span>
                ) : (
                    <div className="flex items-center gap-3">
                        <span
                            className={clsx(
                                CHIP,
                                'min-w-0 truncate',
                                tint === null ? UNTINTED : tint.chip,
                            )}
                        >
                            {place.station}
                        </span>
                        {walk > 0 && (
                            <span className="ml-auto shrink-0 text-row text-hush tabular-nums">
                                <span className="font-medium text-soft">{walk}</span> min walk
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default PlaceCard;
