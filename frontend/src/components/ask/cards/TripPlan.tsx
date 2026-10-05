import Plan from './Plan';
import Stamp from './Stamp';
import { useState } from 'react';
import { Bookmark } from 'lucide-react';
import Spin from '@/components/layout/Spin';
import { isKept, saveTrip } from '@/lib/pace';
import { SURFACE } from '@/components/ask/tints';
import { FAILED_MS, useMoment } from '@/hooks/useMoment';
import { BUBBLE, STAMP } from '@/components/layout/tints';
import type { Level, TripCard } from '@/types/answer';

interface TripPlanProps {
    card: TripCard;
    risk: Level | null;
    chance: number | null;
    refresh: () => Promise<boolean>;
    refreshing: boolean;
}

function TripPlan({ card, risk, chance, refresh, refreshing }: TripPlanProps) {
    const [saved, setSaved] = useState(() => isKept(card.origin, card.destination));
    const [failed, setFailed] = useMoment<'save' | 'refresh' | null>(null, FAILED_MS);

    const keep = async () => {
        if (saved) return;

        setSaved(true);
        setFailed(null);
        try {
            await saveTrip(card.origin, card.destination);
        } catch (error) {
            console.error(error);
            setSaved(false);
            setFailed('save');
        }
    };

    const tryAgain = async () => {
        setFailed(null);
        if (!(await refresh())) setFailed('refresh');
    };

    return (
        <div className={`${SURFACE} flex flex-col gap-3.5 pt-6.5 pb-5`}>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2.5">
                <div className="flex-auto truncate text-title text-bright">
                    {card.origin} <span className="font-medium text-hush">to</span>{' '}
                    {card.destination}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                    <button
                        type="button"
                        onClick={keep}
                        aria-disabled={saved}
                        title={saved ? 'Saved' : 'Save this trip'}
                        aria-label={saved ? 'Saved' : 'Save this trip'}
                        className={`${BUBBLE} self-stretch px-2.75 aria-disabled:pointer-events-none`}
                    >
                        <Bookmark
                            size={12}
                            strokeWidth={2.4}
                            fill={saved ? 'currentColor' : 'none'}
                            className={saved ? 'text-accent' : 'text-quiet'}
                        />
                    </button>
                    <button
                        type="button"
                        onClick={tryAgain}
                        title="Refresh this plan"
                        aria-label="Refresh this plan"
                        className={STAMP}
                    >
                        <Stamp card={card} />
                        <Spin on={refreshing} />
                    </button>
                </div>
            </div>
            {failed !== null && (
                <span role="alert" className="-mt-1.5 text-row text-red">
                    {failed === 'save'
                        ? "Couldn't save this trip. Try again."
                        : "Couldn't refresh this plan. Showing the last one."}
                </span>
            )}
            <Plan card={card} risk={risk} chance={chance} />
        </div>
    );
}

export default TripPlan;
