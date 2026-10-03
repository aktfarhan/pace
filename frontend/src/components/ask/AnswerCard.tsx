import clsx from 'clsx';
import { linesOf } from '@/lib/answer';
import { RISE, SURFACE } from './tints';
import TripPlan from './cards/TripPlan';
import FirstLast from './cards/FirstLast';
import { sourcesOf } from '@/lib/sources';
import type { Answer } from '@/types/answer';

interface AnswerCardProps {
    answer: Answer;
    refresh: () => Promise<boolean>;
    refreshing: boolean;
    fresh: boolean;
}

function AnswerCard({ answer, refresh, refreshing, fresh }: AnswerCardProps) {
    const sources = sourcesOf(answer.sources);

    // Build the body of the answer
    let body;
    if (answer.card?.kind === 'trip') {
        body = (
            <TripPlan
                card={answer.card}
                risk={answer.risk}
                chance={answer.chance}
                refresh={refresh}
                refreshing={refreshing}
            />
        );
    } else if (answer.card?.kind === 'edge') {
        body = <FirstLast card={answer.card} />;
    } else {
        body = (
            <div className={`${SURFACE} flex flex-col gap-2 py-5.5 text-sm/relaxed text-pretty`}>
                {linesOf(answer.answer).map((line, index) =>
                    line.bullet ? (
                        <p key={index} className="flex gap-2.5">
                            <span className="mt-2.25 size-1 shrink-0 rounded-full bg-hush" />
                            {line.text}
                        </p>
                    ) : (
                        <p key={index}>{line.text}</p>
                    ),
                )}
            </div>
        );
    }

    return (
        <div className={clsx('flex flex-col gap-2', fresh && RISE)}>
            {body}
            {sources.length > 0 && (
                <p className="px-5 font-mono text-label text-hush uppercase sm:px-7">
                    Based on {sources.join(' · ')}
                </p>
            )}
        </div>
    );
}

export default AnswerCard;
