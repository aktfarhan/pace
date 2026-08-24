import { readPlaces } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { SavedPlace } from '@/types/place';

export function usePlaces() {
    const [places, setPlaces] = useState<SavedPlace[] | null>(null);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setPlaces(await readPlaces(control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                }
            }
        }

        read();
        return () => control.abort();
    }, []);

    return places;
}
