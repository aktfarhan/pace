import { LINES } from '@/lib/lines';
import type { Tab } from '@/components/transit/tints';

// Storage key for the chart's last picked view
const SPAN_KEY = 'pace.span';

// Storage key for the landing page
const START_KEY = 'pace.start';

// Storage key for the Transit tab
const LINE_KEY = 'pace.line';

// The options for the landing page
export const STARTS = ['Ask', 'Transit', 'Saved'] as const;
export type Start = (typeof STARTS)[number];

// Reads a saved setting
function readStored(key: string) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

// Saves or deletes a setting
function writeStored(key: string, value: string | null) {
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
