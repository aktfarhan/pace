import clsx from 'clsx';
import { RISE } from './tints';
import TurnBody from './TurnBody';
import Starters from './Starters';
import { useLayoutEffect, useRef, useState } from 'react';
import type { Turn } from '@/types/turn';
import type { Stage } from '@/types/answer';
import type { SystemStatus } from '@/types/status';

interface TurnListProps {
    turns: Turn[];
    stage: Stage | null;
    refresh: (id: number, query: string, failed: boolean) => Promise<boolean>;
    refreshing: number | null;
    ask: (query: string) => void;
    status: SystemStatus | null;
}

function TurnList({ turns, stage, refresh, refreshing, ask, status }: TurnListProps) {
    const list = useRef<HTMLDivElement>(null);

    // New questions fade in
    const [known] = useState(() => {
        const settled = turns.filter((turn) => turn.answer !== null || turn.failed);
        return settled.length === 0 ? -1 : settled[settled.length - 1].id;
    });

    // Whether the newest answer is in
    const landed = turns.length > 0 && turns[turns.length - 1].answer !== null;

    // Keep the newest question at the top of the view
    useLayoutEffect(() => {
        const node = list.current;
        if (node === null) return;
        const last = node.lastElementChild;
        if (last === null) return;
        node.scrollTop += last.getBoundingClientRect().top - node.getBoundingClientRect().top;
    }, [turns.length, landed]);

    // Before the first question, make suggestions
    if (turns.length === 0) return <Starters ask={ask} status={status} />;

    return (
        <div
            ref={list}
            className="relative flex flex-1 scroll-edges flex-col gap-6 overflow-y-auto overscroll-contain"
        >
            <h1 className="sr-only">Ask</h1>
            {turns.map((turn) => (
                <div key={turn.id} className="flex flex-col gap-2">
                    <p
                        className={clsx(
                            'max-w-md self-end rounded-tile bg-field px-4.5 py-3 text-sm/snug wrap-break-word text-cream',
                            turn.id > known && RISE,
                        )}
                    >
                        {turn.query}
                    </p>
                    <TurnBody
                        turn={turn}
                        stage={stage}
                        refresh={() => refresh(turn.id, turn.query, turn.failed)}
                        refreshing={refreshing === turn.id}
                        fresh={turn.id > known}
                    />
                </div>
            ))}
        </div>
    );
}

export default TurnList;
