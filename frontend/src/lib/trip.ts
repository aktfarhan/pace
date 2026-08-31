import type { Wait, TripCard, WalkLeg, RideLeg } from '@/types/answer';

// The lines the tints key on
type Line = 'red' | 'orange' | 'green' | 'blue' | 'commuter' | 'bus';

// One slice of the trip bar
interface Segment {
    fill: string;
    share: number;
}

// The route name in a ride's row
export const LINE_TEXT: Record<Line, string> = {
    red: 'text-red',
    orange: 'text-orange',
    green: 'text-green',
    blue: 'text-blue',
    commuter: 'text-commuter',
    bus: 'text-bus',
};

// A ride's chunk of the leg bar
const LINE_FILLS: Record<Line, string> = {
    red: 'bg-red-fill',
    orange: 'bg-orange-fill',
    green: 'bg-green-fill',
    blue: 'bg-blue-fill',
    commuter: 'bg-commuter-fill',
    bus: 'bg-bus-fill',
};

// A station's chip on a saved place
export const LINE_CHIPS: Record<Line, string> = {
    red: 'border-red-fill/28 bg-red-fill/12 text-red',
    orange: 'border-orange-fill/28 bg-orange-fill/12 text-orange',
    green: 'border-green-fill/28 bg-green-fill/12 text-green',
    blue: 'border-blue-fill/28 bg-blue-fill/12 text-blue',
    commuter: 'border-commuter-fill/28 bg-commuter-fill/12 text-commuter',
    bus: 'border-bus-fill/28 bg-bus-fill/12 text-bus',
};

// A ride's icon tile
export const LINE_TILES: Record<Line, string> = {
    red: 'border-red/28 bg-red/12 text-red',
    orange: 'border-orange/28 bg-orange/12 text-orange',
    green: 'border-green/30 bg-green/12 text-green',
    blue: 'border-blue/28 bg-blue/12 text-blue',
    commuter: 'border-commuter/28 bg-commuter/12 text-commuter',
    bus: 'border-bus/28 bg-bus/12 text-bus',
};

const LEAVE_NOW_MINUTES = 5;

// Minutes of waiting before the wait means no service
const NO_SERVICE_MINUTES = 60;

// Minutes of a gap between legs gets its own row
const WAIT_ROW_MINUTES = 10;

// route_id -> the line, or null for buses
export function lineOf(routeId: string): Line | null {
    if (routeId === 'Red' || routeId === 'Mattapan') {
        return 'red';
    }
    if (routeId === 'Orange') {
        return 'orange';
    }
    if (routeId === 'Blue') {
        return 'blue';
    }
    if (routeId.startsWith('Green')) {
        return 'green';
    }
    if (routeId.startsWith('CR-')) {
        return 'commuter';
    }
    if (/^\d+$/.test(routeId)) {
        return 'bus';
    }
    return null;
}

// Formatter
const CLOCK = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' });

// Split time and meridiem
export function clockParts(iso: string) {
    const [time, meridiem] = CLOCK.format(new Date(iso)).split(/\s/);
    return { time, meridiem };
}

// For the time alone
export function clock(iso: string) {
    return clockParts(iso).time;
}

// The whole time
export function fullClock(iso: string) {
    const { time, meridiem } = clockParts(iso);
    return `${time} ${meridiem}`;
}

// Whole minutes between two times
export function minutesBetween(depart: string, arrive: string) {
    return Math.ceil((Date.parse(arrive) - Date.parse(depart)) / 60000);
}

// The legs and the waits between them
export function segmentsOf(card: TripCard): Segment[] {
    const start = Date.parse(card.depart);
    const total = Date.parse(card.arrive) - start;

    const segments: Segment[] = [];
    let previousArrive = start;
    for (const leg of card.legs) {
        const depart = Date.parse(leg.depart);
        const arrive = Date.parse(leg.arrive);

        // The wait before this leg is its own slice
        if (depart > previousArrive) {
            segments.push({ fill: 'bg-edge', share: ((depart - previousArrive) / total) * 100 });
        }

        const line = leg.kind === 'ride' ? lineOf(leg.route_id) : null;
        const fill = line === null ? 'bg-quiet' : LINE_FILLS[line];
        segments.push({ fill, share: ((arrive - depart) / total) * 100 });
        previousArrive = arrive;
    }
    return segments;
}

// The legs in travel order, with the long waits listed
export function timelineOf(card: TripCard): (WalkLeg | RideLeg | Wait)[] {
    const rows: (WalkLeg | RideLeg | Wait)[] = [];
    let previous = null;
    for (const leg of card.legs) {
        if (previous !== null) {
            const gap = Date.parse(leg.depart) - Date.parse(previous.arrive);
            if (gap >= WAIT_ROW_MINUTES * 60000) {
                rows.push({
                    kind: 'wait',
                    station: previous.destination,
                    depart: previous.arrive,
                    arrive: leg.depart,
                });
            }
        }
        rows.push(leg);
        previous = leg;
    }
    return rows;
}

// The weekday a service date lands on
function dayOf(serviceDate: string) {
    const day = new Date(`${serviceDate}T12:00:00`);
    return day.toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase();
}

// Whether the service day is past today
function laterDay(serviceDate: string, now: number) {
    const today = new Date(now);
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const dayNumber = String(today.getDate()).padStart(2, '0');
    return serviceDate > `${today.getFullYear()}-${month}-${dayNumber}`;
}

// The leave line
export function leaveOf(card: TripCard, now: number) {
    // A boarded first ride ends the plan
    const ride = card.legs.find((leg) => leg.kind === 'ride');
    if (ride !== undefined && Date.parse(ride.depart) < now) {
        return { kind: 'departed', label: 'THIS TRIP', time: 'DEPARTED', unit: null };
    }

    const wait = (Date.parse(card.depart) - now) / 60000;
    if (wait <= LEAVE_NOW_MINUTES) {
        const minutes = minutesBetween(card.depart, card.arrive);
        return { kind: 'now', label: 'LEAVE NOW', time: `${minutes}`, unit: 'MIN' };
    }

    // Deadline plans show the latest time to leave, and the day if not today
    if (card.deadline !== null) {
        const day = laterDay(card.service_date, now) ? ` ${dayOf(card.service_date)}` : '';
        const { time, meridiem } = clockParts(card.depart);
        return { kind: 'by', label: `LEAVE BY${day}`, time, unit: meridiem };
    }

    // Plans for another day show that day
    if (laterDay(card.service_date, now)) {
        const { time, meridiem } = clockParts(card.depart);
        return { kind: 'day', label: dayOf(card.service_date), time, unit: meridiem };
    }

    // Under an hour, show leave in minutes
    if (wait <= NO_SERVICE_MINUTES) {
        return { kind: 'in', label: 'LEAVE IN', time: `${Math.ceil(wait)}`, unit: 'MIN' };
    }

    // Over an hour, nothing is running
    return { kind: 'none', label: 'RIGHT NOW', time: 'NO SERVICE', unit: null };
}
