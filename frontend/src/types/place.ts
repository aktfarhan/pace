// A saved place and the closest station it walks to
export interface SavedPlace {
    id: number;
    label: string;
    address: string;
    station: string | null;
    route_id: string | null;
    walk_seconds: number | null;
}
