import { readBoard, removeTrip } from '@/lib/pace';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Planned } from '@/types/trip';

export function useTrips() {
    const [trips, setTrips] = useState<Planned[] | null>(null);
    const [readAt, setReadAt] = useState('');
    const [reading, setReading] = useState(false);
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
        }
    }, []);

    useEffect(() => {
        const control = new AbortController();

        async function start() {
            await read(control.signal);
        }

        start();
        return () => control.abort();
    }, [read]);

    // One re-plan at a time
    async function refresh() {
        if (runningRef.current) return;

        runningRef.current = true;
        setReading(true);
        await read(new AbortController().signal);
        runningRef.current = false;
        setReading(false);
    }

    async function drop(id: number) {
        await removeTrip(id);
        setTrips((saved) => (saved ?? []).filter((trip) => trip.id !== id));
    }

    return { trips, readAt, reading, refresh, drop };
}
