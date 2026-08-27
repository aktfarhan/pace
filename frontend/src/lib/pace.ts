import type { SavedTrip } from '@/types/trip';
import type { SavedPlace } from '@/types/place';
import type { SystemStatus } from '@/types/status';
import type { Answer, Stage } from '@/types/answer';

const API = 'http://localhost:8000';

// Where the code is kept
const CODE_KEY = 'pace.code';

// Longest gap allowed between frames before the request is dropped
const IDLE_MS = 60000;

// How long a save may hang
const SAVE_MS = 15000;

// What each line of a server-sent event opens with
const EVENT_PREFIX = 'event: ';
const DATA_PREFIX = 'data: ';

// One event and data pair from the stream
interface Frame {
    event: string;
    data: string;
}

// Splits one server-sent event into its name and data
function readFrame(frame: string): Frame | null {
    let event = '';
    let data = '';
    for (const line of frame.split('\n')) {
        const clean = line.trimEnd();
        if (clean.startsWith(EVENT_PREFIX)) {
            event = clean.slice(EVENT_PREFIX.length);
        } else if (clean.startsWith(DATA_PREFIX)) {
            data = clean.slice(DATA_PREFIX.length);
        }
    }
    return event ? { event, data } : null;
}

// Hands one frame to the caller, returning the answer if it carried one
function applyFrame(frame: Frame, onStage: (name: Stage) => void): Answer | null {
    const payload = JSON.parse(frame.data);
    if (frame.event === 'error') {
        throw new Error(payload.message);
    }
    if (frame.event === 'stage') {
        onStage(payload.name);
    }
    if (frame.event === 'answer') {
        return payload;
    }
    return null;
}

// The header carrying the code
function codeHeader(): Record<string, string> {
    const code = localStorage.getItem(CODE_KEY);
    return code === null ? {} : { 'X-Pace-Code': code };
}

// Reads the places saved against a code
export async function readPlaces(signal: AbortSignal): Promise<SavedPlace[]> {
    const response = await fetch(`${API}/v1/places`, { signal, headers: codeHeader() });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Saves one place, keeping the code it comes back with
export async function savePlace(label: string, address: string): Promise<SavedPlace> {
    const control = new AbortController();
    const timer = setTimeout(() => control.abort(), SAVE_MS);

    try {
        const response = await fetch(`${API}/v1/places`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...codeHeader() },
            body: JSON.stringify({ label, address }),
            signal: control.signal,
        });
        if (!response.ok) {
            throw new Error(`Pace returned ${response.status}`);
        }

        const saved = await response.json();

        if (typeof saved.code === 'string') localStorage.setItem(CODE_KEY, saved.code);
        return saved.place;
    } finally {
        clearTimeout(timer);
    }
}

// Reads the trips saved against a code
export async function readTrips(signal: AbortSignal): Promise<SavedTrip[]> {
    const response = await fetch(`${API}/v1/trips`, { signal, headers: codeHeader() });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Reads every line's state
export async function readStatus(signal: AbortSignal): Promise<SystemStatus> {
    const response = await fetch(`${API}/v1/status`, { signal });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Sends the question and reports each stage until the answer arrives
export async function ask(query: string, onStage: (name: Stage) => void): Promise<Answer> {
    // The idle timer is set before the fetch
    const control = new AbortController();
    let idle = setTimeout(() => control.abort(), IDLE_MS);

    try {
        const response = await fetch(`${API}/v1/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
            signal: control.signal,
        });

        if (!response.ok) {
            throw new Error(`Pace returned ${response.status}`);
        }
        if (!response.body) {
            throw new Error('Pace sent no stream');
        }

        const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = '';
        let answer: Answer | null = null;

        for (;;) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }

            // Any byte proves the stream is alive, and restart the timer
            clearTimeout(idle);
            idle = setTimeout(() => control.abort(), IDLE_MS);
            buffer += value;

            // A blank line ends an event; the tail is still arriving
            const frames = buffer.split('\n\n');
            buffer = frames.pop() ?? '';

            for (const text of frames) {
                const frame = readFrame(text);
                if (frame === null) {
                    continue;
                }
                answer = applyFrame(frame, onStage) ?? answer;
            }
        }

        if (answer === null) {
            throw new Error('Pace closed the stream without answering');
        }
        return answer;
    } finally {
        clearTimeout(idle);
    }
}
