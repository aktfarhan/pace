import type { TripCard } from '@/types/answer';

// The lines the tints key on
export type Line = 'red' | 'orange' | 'green' | 'blue' | 'commuter';

// The route name in a ride's row
export const LINE_TEXT: Record<Line, string> = {
    red: 'text-red',
    orange: 'text-orange',
    green: 'text-green',
    blue: 'text-blue',
    commuter: 'text-commuter',
};

// A ride's chunk of the leg bar
export const LINE_FILLS: Record<Line, string> = {
    red: 'bg-red-fill',
    orange: 'bg-orange-fill',
    green: 'bg-green-fill',
    blue: 'bg-blue-fill',
    commuter: 'bg-commuter-fill',
};

// A ride's icon tile
export const LINE_TILES: Record<Line, string> = {
    red: 'border-red/28 bg-red/12 text-red',
    orange: 'border-orange/28 bg-orange/12 text-orange',
    green: 'border-green/30 bg-green/12 text-green',
    blue: 'border-blue/28 bg-blue/12 text-blue',
    commuter: 'border-commuter/28 bg-commuter/12 text-commuter',
};

const LEAVE_NOW_MINUTES = 5;

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

// A clock time to leave by, or the trip length
export function heroOf(card: TripCard, now: number) {
    const wait = (Date.parse(card.depart) - now) / 60000;
    if (wait <= LEAVE_NOW_MINUTES) {
        const minutes = minutesBetween(card.depart, card.arrive);
        return { label: 'LEAVE NOW', time: `${minutes}`, unit: 'MIN' };
    }
    const { time, meridiem } = clockParts(card.depart);
    return { label: 'LEAVE BY', time, unit: meridiem };
}
