import { useSyncExternalStore } from 'react';

// The query
let draft = '';
const listeners = new Set<() => void>();

// The question box's current text
const current = () => draft;

// Changes the draft and tells every listener
export function setDraft(next: string) {
    draft = next;
    listeners.forEach((one) => one());
}

// Starts telling one listener about changes
function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}

// The draft
export function useDraft() {
    return useSyncExternalStore(subscribe, current);
}
