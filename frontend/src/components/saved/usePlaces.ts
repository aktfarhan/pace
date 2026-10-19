import { useEffect, useState } from 'react';
import { readPlaces, removePlace, savePlace } from '@/lib/pace';
import type { SavedPlace } from '@/types/place';

export function usePlaces() {
    const [places, setPlaces] = useState<SavedPlace[] | null>(null);
    const [failed, setFailed] = useState(false);
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setPlaces(await readPlaces(control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                    setFailed(true);
                }
            }
        }

        read();
        return () => control.abort();
    }, [attempt]);

    // Reads the places again
    const retry = () => {
        setFailed(false);
        setAttempt((count) => count + 1);
    };

    async function keep(label: string, address: string) {
        const place = await savePlace(label, address);
        if (places === null) retry();
        else setPlaces((saved) => saved && [...saved, place]);
    }

    async function drop(id: number) {
        await removePlace(id);
        setPlaces((saved) => saved && saved.filter((place) => place.id !== id));
    }

    return { places, failed, retry, keep, drop };
}
