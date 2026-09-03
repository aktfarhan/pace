import { ask } from '@/lib/pace';
import { keep } from '@/lib/history';
import { useCallback, useRef, useState } from 'react';
import type { Stage } from '@/types/answer';
import type { Turn, TurnFields } from '@/types/turn';

export type AskController = ReturnType<typeof useAsk>;

// Holds the conversation and runs one question at a time
export function useAsk() {
    const [turns, setTurns] = useState<Turn[]>([]);
    const [busy, setBusy] = useState(false);

    // The stage the open question is on
    const [stage, setStage] = useState<Stage | null>(null);

    // The turn being asked again
    const [refreshing, setRefreshing] = useState<number | null>(null);

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
            setStage(null);

            // Open the turn this question fills in
            const id = nextId.current;
            nextId.current += 1;
            setTurns((old) => [...old, { id, query: asked, answer: null, failed: false }]);

            try {
                const answer = await ask(asked, setStage);
                amend(id, { answer });
                keep(asked, answer);
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

    // Runs a turn's question again and swaps the answer in place
    const refresh = useCallback(
        async (id: number, query: string) => {
            if (running.current) {
                return;
            }

            running.current = true;
            setBusy(true);
            setRefreshing(id);

            try {
                const answer = await ask(query, () => {});
                amend(id, { answer });
            } catch (error) {
                console.error(error);
            } finally {
                running.current = false;
                setBusy(false);
                setRefreshing(null);
            }
        },
        [amend],
    );

    return { turns, stage, busy, send, refresh, refreshing };
}
