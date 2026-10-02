import Leave from './Leave';
import LegBar from './LegBar';
import Summary from './Summary';
import Timeline from './Timeline';
import type { Level, TripCard } from '@/types/answer';

interface PlanProps {
    card: TripCard;
    risk: Level | null;
    chance: number | null;
}

function Plan({ card, risk, chance }: PlanProps) {
    return (
        <>
            <div>
                <Leave card={card} />
                <div className="mt-3 flex flex-col gap-1.75">
                    <LegBar card={card} />
                    <Summary card={card} risk={risk} chance={chance} />
                </div>
            </div>
            <Timeline card={card} />
        </>
    );
}

export default Plan;
