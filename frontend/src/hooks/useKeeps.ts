import { useSyncExternalStore } from 'react';
import { keepsHistory, onKeeping } from '@/lib/prefs';

// Whether questions are kept
export function useKeeps() {
    return useSyncExternalStore(onKeeping, keepsHistory);
}
