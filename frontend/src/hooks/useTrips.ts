import { readTrips } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { SavedTrip } from '@/types/trip';

export function useTrips() {
    const [trips, setTrips] = useState<SavedTrip[] | null>(null);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setTrips(await readTrips(control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                }
            }
        }

        read();
        return () => control.abort();
    }, []);

    return trips;
}
