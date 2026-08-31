import { readBoard, removeTrip } from '@/lib/pace';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Planned } from '@/types/trip';

// How often the board re-plans itself
const REFRESH_MS = 30000;

export function useTrips() {
    const [trips, setTrips] = useState<Planned[] | null>(null);
    const [readAt, setReadAt] = useState('');
    const [reading, setReading] = useState(false);
    const [reads, setReads] = useState(0);
    const runningRef = useRef(false);

    // Re-plans every saved trip
    const read = useCallback(async (signal: AbortSignal) => {
        try {
            setTrips(await readBoard(signal));
            setReadAt(new Date().toISOString());
        } catch (error) {
            if (!signal.aborted) {
                console.error(error);
            }
        } finally {
            setReads((count) => count + 1);
        }
    }, []);

    // One re-plan at a time
    const replan = useCallback(
        async (signal: AbortSignal) => {
            if (runningRef.current) return;

            runningRef.current = true;
            setReading(true);
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

    // Timed from when the last read finished
    useEffect(() => {
        const control = new AbortController();
        const timer = setTimeout(() => replan(control.signal), REFRESH_MS);

        return () => {
            clearTimeout(timer);
            control.abort();
        };
    }, [reads, replan]);

    function refresh() {
        replan(new AbortController().signal);
    }

    async function drop(id: number) {
        await removeTrip(id);
        setTrips((saved) => (saved ?? []).filter((trip) => trip.id !== id));
    }

    return { trips, readAt, reading, refresh, drop };
}
