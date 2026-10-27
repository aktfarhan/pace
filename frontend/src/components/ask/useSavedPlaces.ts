import { readPlaces } from '@/lib/pace';
import { useEffect, useSyncExternalStore } from 'react';
import type { SavedPlace } from '@/types/place';

// How long a read may hang
const READ_MS = 15000;

// The saved places the Ask page shows as chips
let places: SavedPlace[] = [];
const listeners = new Set<() => void>();

// The read in flight, shared by the box and the chat
let reading: Promise<void> | null = null;

// The places read so far
const current = () => places;

// Starts telling one listener about new places
function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}

// Reads the places again, once for every caller
function read() {
    reading ??= readPlaces(AbortSignal.timeout(READ_MS))
        .then((next) => {
            places = next;
            listeners.forEach((one) => one());
        })
        .catch((error) => console.error(error))
        .finally(() => {
            reading = null;
        });
}

// The user's saved places, read again each time the Ask page opens
export function useSavedPlaces() {
    useEffect(read, []);
    return useSyncExternalStore(subscribe, current);
}
