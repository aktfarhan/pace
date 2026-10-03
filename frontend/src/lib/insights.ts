import { KEPT } from '@/lib/history';
import type { Entry } from '@/types/history';
import type { Intent } from '@/types/answer';

// What a question counts as
export type Kind = Intent | 'refused';

// The intent one question counts as
export function entryKind(entry: Entry): Kind {
    return entry.refused ? 'refused' : entry.intent;
}

const HOUR = new Intl.DateTimeFormat('en-US', { hour: 'numeric' });

// The order kinds stack in
const ORDER: Kind[] = [
    'route',
    'schedule',
    'alert',
    'parking-rules',
    'info',
    'off-topic',
    'refused',
];

// An hour's name on the day
function hourName(hour: number) {
    return HOUR.format(new Date(2000, 0, 1, hour));
}

// A day's own name for lookups
export function dayKey(at: string | number) {
    const day = new Date(at);
    return `day-${day.getFullYear()}-${day.getMonth() + 1}-${day.getDate()}`;
}

// One bar is an hour
export interface Tally {
    key: string;
    label: string;
    name: string;
    current: boolean;
    total: number;
    parts: [Kind, number][];
    later: boolean;
}

// The midnight of this day
function dayStart(at: number) {
    const day = new Date(at);
    day.setHours(0, 0, 0, 0);
    return day.getTime();
}

// Each kind's count among some questions
function partsOf(some: Entry[]) {
    return ORDER.map((kind): [Kind, number] => [
        kind,
        some.filter((entry) => entryKind(entry) === kind).length,
    ]).filter(([, count]) => count > 0);
}

// Today hour by hour
export function todayOf(entries: Entry[]): Tally[] {
    const now = new Date();
    const start = dayStart(now.getTime());
    const today = entries.filter((entry) => dayStart(Date.parse(entry.at)) === start);

    const hours: Tally[] = [];
    for (let hour = 0; hour < 24; hour += 1) {
        const some = today.filter((entry) => new Date(entry.at).getHours() === hour);
        const clock = hourName(hour);
        hours.push({
            key: `hour-${hour}`,
            label: hour % 6 === 0 ? clock.replace(/\s/, '').slice(0, -1) : '',
            name: clock,
            current: hour === now.getHours(),
            total: some.length,
            parts: partsOf(some),
            later: hour > now.getHours(),
        });
    }
    return hours;
}

// A full log's oldest question, or null when there's still room
function droppedBefore(entries: Entry[]) {
    return entries.length >= KEPT
        ? Math.min(...entries.map((entry) => Date.parse(entry.at)))
        : null;
}

// Number of questions in a window
function countBetween(entries: Entry[], start: number, end: number) {
    const cut = droppedBefore(entries);
    if (cut !== null && cut > start) return 0;

    return entries.filter((entry) => {
        const at = Date.parse(entry.at);
        return at >= start && at < end;
    }).length;
}

// Yesterday's questions at this time
function yesterdayOf(entries: Entry[]) {
    const end = new Date();
    end.setDate(end.getDate() - 1);
    const start = new Date(end);
    start.setHours(0, 0, 0, 0);

    return countBetween(entries, start.getTime(), end.getTime());
}

// Today against yesterday at this time
export function versusYesterday(entries: Entry[], asked: number) {
    const before = yesterdayOf(entries);
    if (before === 0) return 'Today so far';

    const change = asked - before;
    if (change === 0) return 'Same as this time yesterday';
    return `${change > 0 ? '↑' : '↓'} ${Math.abs(change)} from this time yesterday`;
}

// A question folded for comparing
export function foldOf(query: string) {
    return query
        .toLowerCase()
        .replace(/[?.!\s]+$/, '')
        .trim()
        .replace(/\s+/g, ' ');
}

// The questions most repeated
export function mostAsked(entries: Entry[], keep: number) {
    const seen = new Map<string, { query: string; count: number }>();
    for (const entry of entries) {
        if (entry.refused) continue;
        const key = foldOf(entry.query);
        const one = seen.get(key);
        if (one === undefined) {
            seen.set(key, { query: entry.query.trim(), count: 1 });
        } else {
            one.count += 1;
        }
    }
    return [...seen.values()]
        .filter((one) => one.count > 1)
        .sort((a, b) => b.count - a.count)
        .slice(0, keep);
}
