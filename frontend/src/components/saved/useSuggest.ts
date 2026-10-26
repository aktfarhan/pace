import { suggestPlaces } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { Suggestion } from '@/types/place';

// Letters typed before anything is suggested
const MIN_TYPED = 3;

// Pause in typing before the search runs
const WAIT_MS = 200;

// What the address search offers for the text typed so far
export function useSuggest(typed: string) {
    const [found, setFound] = useState<Suggestion[]>([]);
    const asked = typed.trim();

    useEffect(() => {
        if (asked.length < MIN_TYPED) return;
        const control = new AbortController();

        // Waits for a pause, then asks
        const timer = setTimeout(async () => {
            try {
                setFound(await suggestPlaces(asked, control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                    setFound([]);
                }
            }
        }, WAIT_MS);

        return () => {
            clearTimeout(timer);
            control.abort();
        };
    }, [asked]);

    return asked.length < MIN_TYPED ? [] : found;
}
