import { useSyncExternalStore } from 'react';

// Drawer open state
let out = false;
const listeners = new Set<() => void>();

// Whether it's out now
export const drawerOpen = () => out;

export function setDrawer(next: boolean) {
    out = next;
    listeners.forEach((one) => one());
}

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}

export function useDrawer() {
    return useSyncExternalStore(subscribe, drawerOpen);
}
