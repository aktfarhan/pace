// A saved place and the closest station it walks to
export interface SavedPlace {
    id: number;
    label: string;
    address: string;
    station: string | null;
    route_id: string | null;
    walk_seconds: number | null;
}

// A place the address search offers while typing
export interface Suggestion {
    place_id: string | null;
    label: string;
    kind: string;
    lat: number;
    lon: number;
}
