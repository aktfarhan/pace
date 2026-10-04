// Storage key for the chart's last picked view
const SPAN_KEY = 'pace.span';

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

// The views the History chart switches between
export const SPANS = ['Day', 'Week'] as const;
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
