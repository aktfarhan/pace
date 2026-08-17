import TurnBody from './TurnBody';
import { useLayoutEffect, useRef } from 'react';
import type { Turn } from '@/types/turn';
import type { Stage } from '@/types/answer';

interface TurnListProps {
    turns: Turn[];
    stage: Stage | null;
    refresh: (id: number, query: string) => void;
    refreshing: number | null;
}

function TurnList({ turns, stage, refresh, refreshing }: TurnListProps) {
    const list = useRef<HTMLDivElement>(null);

    // Scroll to the newest turn
    useLayoutEffect(() => {
        const node = list.current;
        if (node !== null) {
            node.scrollTop = node.scrollHeight;
        }
    }, [turns.length]);

    return (
        <div ref={list} className="flex flex-1 flex-col gap-6 overflow-y-auto">
            {turns.map((turn) => (
                <div key={turn.id} className="flex flex-col gap-2">
                    <p className="max-w-md self-end rounded-2xl rounded-br-sm border border-edge bg-bubble px-4 py-2.5 text-sm text-cream">
                        {turn.query}
                    </p>
                    <TurnBody
                        turn={turn}
                        stage={stage}
                        refresh={() => refresh(turn.id, turn.query)}
                        refreshing={refreshing === turn.id}
                    />
                </div>
            ))}
        </div>
    );
}

export default TurnList;
