import { useState } from 'react';
import { useUndo } from './useUndo';

// Remove a saved place or trip
export function useRemoval(drop: (id: number) => Promise<void>, id: number) {
    const [removing, setRemoving] = useState(false);
    const { pending, start, undo } = useUndo();

    const commit = async () => {
        setRemoving(true);
        try {
            await drop(id);
        } catch (error) {
            console.error(error);
            setRemoving(false);
        }
    };

    return {
        going: pending || removing,
        remove: () => start(commit),
        undo: pending ? undo : null,
    };
}
