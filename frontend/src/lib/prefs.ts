import { LINES } from '@/lib/lines';
import type { Tab } from '@/components/transit/tints';

// Storage key for the chart's last picked view
const SPAN_KEY = 'pace.span';

// Storage key for the landing page
const START_KEY = 'pace.start';

// Storage key for the Transit tab
const LINE_KEY = 'pace.line';

// Storage key for the keeping choice
const KEEP_KEY = 'pace.keep';

// The event a keeping switch sends
const KEEPING = 'pace:keep';

// The options for the landing page
export const STARTS = ['Ask', 'Transit', 'Saved'] as const;
export type Start = (typeof STARTS)[number];

// Reads a saved setting
export function readStored(key: string) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

// Saves or deletes a setting
export function writeStored(key: string, value: string | null) {
    try {
        if (value === null) localStorage.removeItem(key);
        else localStorage.setItem(key, value);
    } catch (error) {
        console.error(error);
    }
}

// The landing page
export function readStart(): Start {
    const start = readStored(START_KEY);
    return STARTS.find((one) => one === start) ?? 'Ask';
}

// Saves the picked start page
export function writeStart(start: Start) {
    writeStored(START_KEY, start === 'Ask' ? null : start);
}

// Whether questions are kept on this device
export function keepsHistory() {
    return readStored(KEEP_KEY) !== 'off';
}

// Saves the keeping choice
export function writeKeepsHistory(on: boolean) {
    writeStored(KEEP_KEY, on ? null : 'off');
    window.dispatchEvent(new Event(KEEPING));
}

// Listens for keeping switches
export function onKeeping(listener: () => void) {
    window.addEventListener(KEEPING, listener);
    return () => window.removeEventListener(KEEPING, listener);
}

// The Transit tab
export function readLine(): Tab {
    const line = readStored(LINE_KEY);
    return LINES.find((one) => one.label === line)?.label ?? 'All';
}

// Saves the picked Transit tab
export function writeLine(line: Tab) {
    writeStored(LINE_KEY, line === 'All' ? null : line);
}

// The views the History chart switches between
export const SPANS = ['Day', 'Week', 'Month'] as const;
export type Span = (typeof SPANS)[number];

// The view History opens on
export function readSpan(): Span {
    const span = readStored(SPAN_KEY);
    return SPANS.find((one) => one === span) ?? 'Week';
}

// Saves the picked view
export function writeSpan(span: Span) {
    writeStored(SPAN_KEY, span === 'Week' ? null : span);
}

// Reset settings to default
export function resetPrefs() {
    for (const key of [START_KEY, KEEP_KEY, LINE_KEY, SPAN_KEY]) writeStored(key, null);
    window.dispatchEvent(new Event(KEEPING));
}
