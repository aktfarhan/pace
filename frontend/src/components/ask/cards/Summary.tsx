import Risk from './Risk';
import Chance from './Chance';
import { useNow } from '@/hooks/useNow';
import { fullClock, leaveOf } from '@/lib/trip';
import type { Level, TripCard } from '@/types/answer';

const META = 'font-mono text-meta whitespace-nowrap text-dim uppercase tabular-nums';

// Each fact has a dot in the gap before it
const FACT = `${META} relative before:absolute before:inset-y-0 before:right-full before:flex before:w-5 before:items-center before:justify-center before:font-sans before:text-base before:leading-none before:tracking-normal before:text-edge before:content-['·']`;

interface SummaryProps {
    card: TripCard;
    risk: Level | null;
    chance: number | null;
}

function Summary({ card, risk, chance }: SummaryProps) {
    const now = useNow();
    const idle = leaveOf(card, now).kind === 'none';

    return (
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 pt-0.75">
            <Risk risk={risk} />
            <Chance chance={chance} />
            <span className="flex-1" />
            <span className="flex min-h-6 flex-wrap items-center gap-x-5 gap-y-1 overflow-hidden">
                {idle && (
                    <span className={FACT}>
                        Next trip{' '}
                        <span className="text-meta-value text-cream">{fullClock(card.depart)}</span>
                    </span>
                )}
                <span className={FACT}>
                    Arrive{' '}
                    <span className="text-meta-value text-cream">{fullClock(card.arrive)}</span>
                </span>
                <span className={FACT}>
                    Transfers <span className="text-meta-value text-cream">{card.transfers}</span>
                </span>
            </span>
        </div>
    );
}

export default Summary;
