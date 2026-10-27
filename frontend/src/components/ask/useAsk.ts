import { ask, Notice, plan } from '@/lib/pace';
import { keep } from '@/lib/history';
import { useCallback, useRef, useState } from 'react';
import type { Picked, Stage } from '@/types/answer';
import type { Turn, TurnFields } from '@/types/turn';

export type AskController = ReturnType<typeof useAsk>;

// What a failure tells the visitor
const saidOf = (error: unknown) => (error instanceof Notice ? error.message : undefined);

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
        async (query: string, pick?: Picked) => {
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
            setTurns((old) => [...old, { id, query: asked, pick, answer: null, failed: false }]);

            try {
                // A picked place plans the trip without reading the question again
                const answer = pick ? await plan(pick) : await ask(asked, setStage);
                amend(id, { answer });
                keep(asked, answer);
            } catch (error) {
                console.error(error);
                amend(id, { failed: true, said: saidOf(error) });
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
        async (turn: Turn) => {
            const { id, query, failed } = turn;
            if (running.current) {
                return true;
            }

            running.current = true;
            setBusy(true);
            setRefreshing(id);

            try {
                // A planned trip is planned again with its ends as found
                const again = turn.answer?.again ?? turn.pick;
                const answer = again ? await plan(again) : await ask(query, () => {});
                if (!failed && answer.card?.kind !== 'trip') return false;

                // The sources the first answer drew on still stand
                const sources = turn.answer?.sources ?? answer.sources;
                amend(id, { answer: { ...answer, sources }, failed: false });

                // Keep the question even tho it failed
                if (failed) keep(query, answer);
                return true;
            } catch (error) {
                console.error(error);
                if (failed) amend(id, { said: saidOf(error) });
                return false;
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
