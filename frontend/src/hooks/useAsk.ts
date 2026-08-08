import { ask } from '@/lib/pace';
import { useCallback, useRef, useState } from 'react';
import type { Stage } from '@/types/answer';
import type { Turn, TurnFields } from '@/types/turn';

export type AskController = ReturnType<typeof useAsk>;

// Holds the conversation and runs one question at a time
export function useAsk() {
    const [turns, setTurns] = useState<Turn[]>([]);
    const [busy, setBusy] = useState(false);

    // The stages of the question
    const [stages, setStages] = useState<Stage[]>([]);

    // Busy is for rendering, and the ref for guarding a double send
    const running = useRef(false);
    const nextId = useRef(0);

    // Writes fields onto one turn, found by id
    const amend = useCallback((id: number, fields: TurnFields) => {
        setTurns((old) =>
            old.map((turn) => {
                if (turn.id !== id) {
                    return turn;
                }
                return { ...turn, ...fields };
            }),
        );
    }, []);

    const send = useCallback(
        async (query: string) => {
            // Nothing to ask, or a question is already running
            const asked = query.trim();
            if (asked === '' || running.current) {
                return;
            }
            running.current = true;
            setBusy(true);
            setStages([]);

            // Open the turn this question fills in
            const id = nextId.current;
            nextId.current += 1;
            setTurns((old) => [...old, { id, query: asked, answer: null, failed: false }]);

            try {
                const answer = await ask(asked, (stage) => {
                    setStages((old) => [...old, stage]);
                });
                amend(id, { answer });
            } catch (error) {
                console.error(error);
                amend(id, { failed: true });
            } finally {
                // Free the guard whether it answered or failed
                running.current = false;
                setBusy(false);
            }
        },
        [amend],
    );

    return { turns, stages, busy, send };
}
