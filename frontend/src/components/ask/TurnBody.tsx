import Thinking from './Thinking';
import AnswerCard from './AnswerCard';
import Failed from '@/components/layout/Failed';
import type { Turn } from '@/types/turn';
import type { Stage } from '@/types/answer';

const WORKING = 'Working';
const UNREACHABLE = "Couldn't get an answer";

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
    // A failed question can be asked again
    if (turn.failed && !refreshing) {
        return <Failed said={UNREACHABLE} retry={refresh} />;
    }
    if (turn.failed || stage === null) {
        return <p className="text-sm text-dim">{WORKING}</p>;
    }
    return <Thinking stage={stage} />;
}

export default TurnBody;
