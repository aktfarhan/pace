import { countUnder } from '@/lib/pace';
import { useEffect, useState } from 'react';

interface Held {
    under: string;
    text: string;
    failed: boolean;
}

// What a code holds
export function useHolding(code: string | null) {
    const [held, setHeld] = useState<Held | null>(null);

    useEffect(() => {
        if (code === null) return;

        // Whether this read still counts
        let live = true;
        countUnder(code)
            // The count in words
            .then(({ places, trips }) => {
                const text = `${places} place${places === 1 ? '' : 's'} and ${trips} trip${trips === 1 ? '' : 's'}`;
                if (live) setHeld({ under: code, text, failed: false });
            })
            // A read that failed
            .catch((error) => {
                console.error(error);
                const text = "What's saved couldn't be read";
                if (live) setHeld({ under: code, text, failed: true });
            });

        // A newer code or a closed page drops it
        return () => {
            live = false;
        };
    }, [code]);

    // A reading for an earlier code doesn't count
    return held?.under === code ? held : null;
}
