import TurnBody from './TurnBody';
import type { Turn } from '@/types/turn';
import type { Stage } from '@/types/answer';

interface TurnListProps {
    turns: Turn[];
    stage: Stage | null;
}

function TurnList({ turns, stage }: TurnListProps) {
    return (
        <div className="flex flex-col gap-6">
            {turns.map((turn) => (
                <div key={turn.id} className="flex flex-col gap-2">
                    <p className="max-w-md self-end rounded-2xl rounded-br-sm border border-edge bg-bubble px-4 py-2.5 text-sm text-cream">
                        {turn.query}
                    </p>
                    <TurnBody turn={turn} stage={stage} />
                </div>
            ))}
        </div>
    );
}

export default TurnList;
