import { readBoard, removeTrip } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { Planned } from '@/types/trip';

export function useTrips() {
    const [trips, setTrips] = useState<Planned[] | null>(null);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setTrips(await readBoard(control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                }
            }
        }

        read();
        return () => control.abort();
    }, []);

    async function drop(id: number) {
        await removeTrip(id);
        setTrips((saved) => (saved ?? []).filter((trip) => trip.id !== id));
    }

    return { trips, drop };
}
