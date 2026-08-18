import TripPlan from './cards/TripPlan';
import FirstLast from './cards/FirstLast';
import type { Answer } from '@/types/answer';

const GROUNDED = 'Grounded';

interface AnswerCardProps {
    answer: Answer;
    refresh: () => void;
    refreshing: boolean;
}

function AnswerCard({ answer, refresh, refreshing }: AnswerCardProps) {
    // Build the body of the answer
    let body;
    if (answer.card?.kind === 'trip') {
        body = <TripPlan card={answer.card} refresh={refresh} refreshing={refreshing} />;
    } else if (answer.card?.kind === 'edge') {
        body = <FirstLast card={answer.card} />;
    } else {
        body = (
            <div className="rounded-card border border-edge bg-field p-4">
                <p className="text-sm/relaxed whitespace-pre-line text-soft">{answer.answer}</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            {body}
            {answer.sources.length > 0 && (
                <p className="pl-1 font-mono text-label text-faint uppercase">
                    {GROUNDED} — {answer.sources.join(' · ')}
                </p>
            )}
        </div>
    );
}

export default AnswerCard;
