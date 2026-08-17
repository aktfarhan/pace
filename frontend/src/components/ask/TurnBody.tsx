import Thinking from './Thinking';
import AnswerCard from './AnswerCard';
import type { Turn } from '@/types/turn';
import type { Stage } from '@/types/answer';

const WORKING = 'Working';
const UNREACHABLE = 'Pace is unreachable. Nothing was retrieved.';

interface TurnBodyProps {
    turn: Turn;
    stage: Stage | null;
    refresh: () => void;
    refreshing: boolean;
}

function TurnBody({ turn, stage, refresh, refreshing }: TurnBodyProps) {
    if (turn.answer !== null) {
        return <AnswerCard answer={turn.answer} refresh={refresh} refreshing={refreshing} />;
    }
    if (turn.failed) {
        return <p className="text-sm text-dim">{UNREACHABLE}</p>;
    }
    if (stage === null) {
        return <p className="text-sm text-dim">{WORKING}</p>;
    }
    return <Thinking stage={stage} />;
}

export default TurnBody;
