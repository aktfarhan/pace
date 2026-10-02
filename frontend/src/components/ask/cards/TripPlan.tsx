import Plan from './Plan';
import Stamp from './Stamp';
import { useState } from 'react';
import { saveTrip } from '@/lib/pace';
import { Bookmark, RotateCw } from 'lucide-react';
import type { Level, TripCard } from '@/types/answer';

interface TripPlanProps {
    card: TripCard;
    risk: Level | null;
    chance: number | null;
    refresh: () => void;
    refreshing: boolean;
}

const PILL =
    'flex shrink-0 cursor-pointer items-center rounded-full border border-edge bg-bubble py-1.75 text-hush transition-colors hover:border-ghost hover:bg-line hover:text-cream';

function TripPlan({ card, risk, chance, refresh, refreshing }: TripPlanProps) {
    const [saved, setSaved] = useState(false);
    const [saving, setSaving] = useState(false);

    const keep = async () => {
        if (saved || saving) return;

        setSaving(true);
        try {
            await saveTrip(card.origin, card.destination);
            setSaved(true);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="flex flex-col gap-3.5 rounded-card border border-edge bg-field px-7 pt-6.5 pb-5 text-cream">
            <div className="flex items-center justify-between gap-4">
                <div className="truncate text-title text-bright">
                    {card.origin} <span className="font-medium text-hush">to</span>{' '}
                    {card.destination}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                    <button
                        type="button"
                        onClick={keep}
                        disabled={saved || saving}
                        title={saved ? 'Saved' : 'Save this trip'}
                        aria-label={saved ? 'Saved' : 'Save this trip'}
                        className={`${PILL} px-2.75 disabled:cursor-default`}
                    >
                        <Bookmark
                            size={12}
                            strokeWidth={2.4}
                            fill={saved ? 'currentColor' : 'none'}
                            className={saved ? 'text-accent' : 'text-quiet'}
                            aria-hidden="true"
                        />
                    </button>
                    <button
                        type="button"
                        onClick={refresh}
                        title="Refresh this plan"
                        className={`${PILL} gap-2 px-3.25`}
                    >
                        <Stamp card={card} />
                        <RotateCw
                            size={12}
                            strokeWidth={2.4}
                            className={refreshing ? 'animate-spin text-quiet' : 'text-quiet'}
                            aria-hidden="true"
                        />
                    </button>
                </div>
            </div>
            <Plan card={card} risk={risk} chance={chance} />
        </div>
    );
}

export default TripPlan;
