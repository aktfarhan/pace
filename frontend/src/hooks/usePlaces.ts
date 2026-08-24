import { useEffect, useState } from 'react';
import { readPlaces, savePlace } from '@/lib/pace';
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

    async function keep(label: string, address: string) {
        const place = await savePlace(label, address);
        setPlaces((saved) => [...(saved ?? []), place]);
    }

    return { places, keep };
}
