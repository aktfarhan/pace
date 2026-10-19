import { poll } from '@/lib/poll';
import { feedStatus } from '@/hooks/useStatus';
import { readReadings, readTransit } from '@/lib/pace';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Readings, Transit } from '@/types/transit';

// The transit page's data, re-read on a timer
export function useTransit() {
    const [transit, setTransit] = useState<Transit | null>(null);
    const [failed, setFailed] = useState(false);
    const [attempt, setAttempt] = useState(0);

    // The readings held, and the name they were sent under
    const held = useRef<{ name: string; readings: Readings } | null>(null);

    // Asking again starts the timer over
    const retry = useCallback(() => {
        setFailed(false);
        setAttempt((count) => count + 1);
    }, []);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                const live = await readTransit(control.signal);

                // The readings change once a quarter hour
                if (held.current?.name !== live.readings) {
                    held.current = {
                        name: live.readings,
                        readings: await readReadings(control.signal),
                    };
                }

                feedStatus(live.status);
                setTransit({ ...live, ...held.current.readings });
                setFailed(false);
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                    setFailed(true);
                }
            }
        }

        const stop = poll(read);
        return () => {
            control.abort();
            stop();
        };
    }, [attempt]);

    return { transit, failed, retry };
}
