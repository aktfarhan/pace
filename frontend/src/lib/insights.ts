import { DAY, KEPT } from '@/lib/history';
import type { Span } from '@/lib/prefs';
import type { Entry } from '@/types/history';
import type { Intent } from '@/types/answer';

// What a question counts as
export type Kind = Intent | 'refused';

// The intent one question counts as
export function entryKind(entry: Entry): Kind {
    return entry.refused ? 'refused' : entry.intent;
}

const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR = new Intl.DateTimeFormat('en-US', { hour: 'numeric' });
const WEEKDAY = new Intl.DateTimeFormat('en-US', { weekday: 'narrow' });
const DAY_NAME = new Intl.DateTimeFormat('en-US', { weekday: 'long' });

// What each span compares against
const BEFORE: Record<
    Span,
    { count: (entries: Entry[]) => number; than: string; first: string | null }
> = {
    Day: { count: yesterdayOf, than: 'this time yesterday', first: 'Today so far' },
    Week: { count: weekBeforeOf, than: 'the week before', first: 'This week' },
    Month: { count: monthBeforeOf, than: 'this time last month', first: null },
};

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
export function hourName(hour: number) {
    return HOUR.format(new Date(2000, 0, 1, hour));
}

// A day's own name for lookups
export function dayKey(at: string | number) {
    const day = new Date(at);
    return `day-${day.getFullYear()}-${day.getMonth() + 1}-${day.getDate()}`;
}

// One bar is an hour or a day
export interface Tally {
    key: string;
    label: string;
    name: string;
    current: boolean;
    total: number;
    parts: [Kind, number][];
    later: boolean;
    lost: boolean;
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
function todayOf(entries: Entry[]): Tally[] {
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
            lost: false,
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

// The questions of each of the last seven days
function weekOf(entries: Entry[]): Tally[] {
    const today = dayStart(Date.now());
    const startOf = (back: number) => dayStart(today - back * DAY_MS + DAY_MS / 2);
    const first = startOf(6);
    const recent = entries.filter((entry) => Date.parse(entry.at) >= first);

    const week: Tally[] = [];
    for (let back = 6; back >= 0; back -= 1) {
        const start = startOf(back);
        const day = recent.filter((entry) => dayStart(Date.parse(entry.at)) === start);
        week.push({
            key: dayKey(start),
            label: WEEKDAY.format(start),
            name: DAY_NAME.format(start),
            current: back === 0,
            total: day.length,
            parts: partsOf(day),
            later: false,
            lost: false,
        });
    }
    return week;
}

// The seven days a week earlier
function weekBeforeOf(entries: Entry[]) {
    const end = new Date();
    end.setDate(end.getDate() - 7);
    const start = new Date(end);
    start.setDate(start.getDate() - 6);
    start.setHours(0, 0, 0, 0);

    return countBetween(entries, start.getTime(), end.getTime());
}

// Every day of this month
function monthOf(entries: Entry[]): Tally[] {
    const now = new Date();
    const today = dayStart(now.getTime());
    const [year, month] = [now.getFullYear(), now.getMonth()];
    const last = new Date(year, month + 1, 0).getDate();

    const first = new Date(year, month, 1).getTime();
    const recent = entries.filter((entry) => Date.parse(entry.at) >= first);

    // Days before this were dropped
    const cut = droppedBefore(entries);

    const days: Tally[] = [];
    for (let day = 1; day <= last; day += 1) {
        const start = new Date(year, month, day).getTime();
        const some = recent.filter((entry) => dayStart(Date.parse(entry.at)) === start);
        days.push({
            key: dayKey(start),
            label: String(day),
            name: DAY.format(start),
            current: start === today,
            total: some.length,
            parts: partsOf(some),
            later: start > today,
            lost: cut !== null && new Date(year, month, day + 1).getTime() <= cut,
        });
    }
    return days;
}

// Last month's questions at this time
function monthBeforeOf(entries: Entry[]) {
    const now = new Date();
    const [year, month] = [now.getFullYear(), now.getMonth()];
    const start = new Date(year, month - 1, 1);
    const length = new Date(year, month, 0).getDate();

    const end =
        now.getDate() > length
            ? new Date(year, month, 1)
            : new Date(
                  year,
                  month - 1,
                  now.getDate(),
                  now.getHours(),
                  now.getMinutes(),
                  now.getSeconds(),
              );

    return countBetween(entries, start.getTime(), end.getTime());
}

// The bars or days for a span
export function tallyOf(span: Span, entries: Entry[]) {
    if (span === 'Day') return todayOf(entries);
    if (span === 'Month') return monthOf(entries);
    return weekOf(entries);
}

// The span's count against the same stretch before it
export function versusBefore(span: Span, entries: Entry[], asked: number) {
    const { count, than, first } = BEFORE[span];
    const before = count(entries);
    if (before === 0) return first;

    const change = asked - before;
    if (change === 0) return `Same as ${than}`;
    return `${change > 0 ? '↑' : '↓'} ${Math.abs(change)} from ${than}`;
}

// Questions counted by the hour asked
export function hoursOf(entries: Entry[]) {
    const hours = new Array<number>(24).fill(0);
    for (const entry of entries) hours[new Date(entry.at).getHours()] += 1;
    return hours;
}

// How many questions each intent took
export function kindsOf(entries: Entry[]) {
    const counts = new Map<Kind, number>();
    for (const entry of entries) {
        const kind = entryKind(entry);
        counts.set(kind, (counts.get(kind) ?? 0) + 1);
    }
    return [...counts].sort((a, b) => b[1] - a[1]);
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
