import { POLL_MS } from '@/lib/poll';
import { readBoard, removeTrip } from '@/lib/pace';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Planned } from '@/types/trip';

export function useTrips() {
    const [trips, setTrips] = useState<Planned[] | null>(null);
    const [readAt, setReadAt] = useState('');
    const [reading, setReading] = useState(false);
    const [reads, setReads] = useState(0);
    const [failed, setFailed] = useState(false);
    const runningRef = useRef(false);

    // Re-plans every saved trip
    const read = useCallback(async (signal: AbortSignal) => {
        try {
            setTrips(await readBoard(signal));
            setReadAt(new Date().toISOString());
            setFailed(false);
        } catch (error) {
            if (!signal.aborted) {
                console.error(error);
                setFailed(true);
            }
        } finally {
            setReads((count) => count + 1);
        }
    }, []);

    // One re-plan at a time
    const replan = useCallback(
        async (signal: AbortSignal, asked = false) => {
            if (asked) {
                setReading(true);
                setFailed(false);
            }
            if (runningRef.current) return;

            runningRef.current = true;
            await read(signal);
            runningRef.current = false;
            setReading(false);
        },
        [read],
    );

    useEffect(() => {
        const control = new AbortController();

        async function start() {
            await read(control.signal);
        }

        start();
        return () => control.abort();
    }, [read]);

    // Timed from the last read
    useEffect(() => {
        const control = new AbortController();
        const again = () => {
            if (document.visibilityState === 'visible') replan(control.signal);
            else document.addEventListener('visibilitychange', again, { once: true });
        };
        const timer = setTimeout(again, POLL_MS);

        return () => {
            clearTimeout(timer);
            control.abort();
            document.removeEventListener('visibilitychange', again);
        };
    }, [reads, replan]);

    function refresh() {
        replan(new AbortController().signal, true);
    }

    async function drop(id: number) {
        await removeTrip(id);
        setTrips((saved) => saved && saved.filter((trip) => trip.id !== id));
    }

    return { trips, readAt, reading, failed, refresh, drop };
}
