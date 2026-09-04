import { fullClock } from '@/lib/trip';
import type { Entry } from '@/types/history';
import type { Answer, Card } from '@/types/answer';

// Where the questions are kept
const HISTORY_KEY = 'pace.history';

// How many questions the device holds
const KEPT = 200;

// Formatter for day title
const DAY = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
});

// A group of questions under a day
interface Day {
    heading: string;
    entries: Entry[];
}

// Reads the questions this device has asked
export function readHistory(): Entry[] {
    try {
        const stored = localStorage.getItem(HISTORY_KEY);
        if (stored === null) {
            return [];
        }
        const parsed = JSON.parse(stored);
        return Array.isArray(parsed) ? (parsed as Entry[]) : [];
    } catch (error) {
        console.error(error);
        return [];
    }
}

// What the row says after its kind
function detailOf(card: Card | null): string {
    if (card === null || card.kind !== 'trip') {
        return '';
    }
    const ends = `${card.origin} to ${card.destination}`;
    if (card.transfers === 0) {
        return ends;
    }
    const plural = card.transfers === 1 ? 'transfer' : 'transfers';
    return `${ends} · ${card.transfers} ${plural}`;
}

// The response pill of each query
function chipOf(card: Card | null, refused: boolean): string | null {
    if (refused) {
        return 'REFUSED';
    }
    if (card === null) {
        return null;
    }
    if (card.kind === 'trip') {
        return `LEAVE ${fullClock(card.depart)}`;
    }
    if (card.kind === 'edge') {
        const first = card.directions[0];
        return first === undefined ? null : fullClock(first.time);
    }
    const soonest = card.departures[0];
    return soonest === undefined ? null : fullClock(soonest.times[0]);
}

// Stores the list
function write(entries: Entry[]) {
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
    } catch (error) {
        console.error(error);
    }
}

// Adds one answered question
export function keep(query: string, answer: Answer) {
    const row: Entry = {
        at: new Date().toISOString(),
        query,
        intent: answer.intent,
        refused: answer.should_refuse,
        detail: detailOf(answer.card),
        chip: chipOf(answer.card, answer.should_refuse),
    };
    write([row, ...readHistory()].slice(0, KEPT));
}

// Clears history
export function clearHistory() {
    write([]);
}

// Heading for today, yesterday, or the date
function headingOf(at: string) {
    const asked = new Date(at);
    const now = new Date();
    if (asked.toDateString() === now.toDateString()) {
        return 'Today';
    }

    now.setDate(now.getDate() - 1);
    if (asked.toDateString() === now.toDateString()) {
        return 'Yesterday';
    }
    return DAY.format(asked);
}

// Group by the day asked
export function daysOf(entries: Entry[]) {
    const days: Day[] = [];
    for (const entry of entries) {
        const heading = headingOf(entry.at);

        // The day still being filled
        const open = days[days.length - 1];
        if (open !== undefined && open.heading === heading) {
            open.entries.push(entry);
            continue;
        }

        // A heading the list has not reached yet
        days.push({ heading, entries: [entry] });
    }
    return days;
}
