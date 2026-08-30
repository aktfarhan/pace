import type { Level, TripCard } from '@/types/answer';

// A saved trip
export interface SavedTrip {
    id: number;
    origin: string;
    destination: string;
}

// One saved trip and the plan it has right now
export interface Planned {
    id: number;
    origin: string;
    destination: string;
    card: TripCard | null;
    risk: Level | null;
}
