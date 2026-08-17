// One route leaving one stop in one direction
export interface Departure {
    route_id: string;
    short_name: string;
    label: string;
    route_type: number;
    station: string;
    destination: string;
    times: string[];
    live: boolean;
}

// What is leaving a stop, soonest first
export interface DeparturesCard {
    kind: 'departures';
    departures: Departure[];
    retrieved_at: string;
}

// One direction's first or last departure
export interface EdgeDirection {
    destination: string;
    time: string;
}

// The first or last departures at a stop, one per direction
export interface EdgeCard {
    kind: 'edge';
    edge: string;
    route_id: string;
    label: string;
    station: string;
    day: string;
    directions: EdgeDirection[];
    retrieved_at: string;
}

// One walk, or a transfer inside a station
export interface WalkLeg {
    kind: 'walk';
    destination: string;
    transfer: boolean;
    depart: string;
    arrive: string;
}

// One ride from boarding to alighting
export interface RideLeg {
    kind: 'ride';
    route_id: string;
    label: string;
    destination: string;
    depart: string;
    arrive: string;
}

// A long wait between legs
export interface Wait {
    kind: 'wait';
    station: string;
    depart: string;
    arrive: string;
}

// One planned trip
export interface TripCard {
    kind: 'trip';
    origin: string;
    destination: string;
    depart: string;
    arrive: string;
    transfers: number;
    live: boolean;
    service_date: string;
    deadline: string | null;
    legs: (WalkLeg | RideLeg)[];
    retrieved_at: string;
}

// The structure an answer draws
export type Card = DeparturesCard | EdgeCard | TripCard;

// What /v1/ask returns
export interface Answer {
    answer: string;
    sources: string[];
    risk: string | null;
    should_refuse: boolean;
    refuse_reason: string | null;
    card: Card | null;
}

// A stage the pipeline reports
export type Stage = 'classify' | 'retrieve' | 'plan' | 'alerts' | 'departures' | 'generate';
