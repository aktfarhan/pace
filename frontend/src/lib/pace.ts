import { readStored, writeStored } from '@/lib/prefs';
import type { Live, Readings } from '@/types/transit';
import type { SavedPlace, Suggestion } from '@/types/place';
import type { SystemStatus } from '@/types/status';
import type { Answer, Picked, Stage, TripCard } from '@/types/answer';
import type { Planned, SavedTrip } from '@/types/trip';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Where the code is kept
const CODE_KEY = 'pace.code';

// Storage key for this device's own code
const WAS_KEY = 'pace.code.was';

// Longest gap allowed between frames before the request is dropped
const IDLE_MS = 60000;

// How long a request may hang
const WRITE_MS = 15000;

// What each line of a server-sent event opens with
const EVENT_PREFIX = 'event: ';
const DATA_PREFIX = 'data: ';

// Trips saved in a visit
const kept = new Set<string>();

// The read of trips already saved under this code
let keptRead: Promise<void> | null = null;

// The first save without a code
let minting: Promise<void> | null = null;

// Code switches so far
let switches = 0;
const SWITCHED = 'pace:switched';

export class Notice extends Error {}

// A request the server turned down
class Refused extends Error {
    status: number;

    constructor(status: number) {
        super(`Pace returned ${status}`);
        this.status = status;
    }
}

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
        throw new Notice(payload.message);
    }
    if (frame.event === 'stage') {
        onStage(payload.name);
    }
    if (frame.event === 'answer') {
        return payload;
    }
    return null;
}

// Reads the code this device saves against
export function readCode(): string | null {
    return readStored(CODE_KEY);
}

// Points this device at another code
function writeCode(code: string) {
    if (code !== readCode()) {
        kept.clear();
        keptRead = null;
    }
    writeStored(CODE_KEY, code);
}

// Reads this device's own code
export function readWas(): string | null {
    return readStored(WAS_KEY);
}

// Switches to another device's code
export function takeCode(code: string) {
    const own = readWas() ?? readCode();
    writeStored(WAS_KEY, own !== null && own !== code ? own : null);
    writeCode(code);
    announce();
}

// Goes back to this device's code
export function undoCode() {
    const own = readWas();
    if (own === null) return;
    writeStored(WAS_KEY, null);
    writeCode(own);
    announce();
}

// Sends the switch event
function announce() {
    switches += 1;
    window.dispatchEvent(new Event(SWITCHED));
}

// The switch count
export function switchesSoFar() {
    return switches;
}

// Listens for code switches
export function onSwitch(heard: () => void) {
    window.addEventListener(SWITCHED, heard);
    return () => window.removeEventListener(SWITCHED, heard);
}

// The header carrying the code
function codeHeader(): Record<string, string> {
    const code = readCode();
    return code === null ? {} : { 'X-Pace-Code': code };
}

// Sends one request, exits if it hangs
async function send(path: string, init: RequestInit): Promise<string> {
    const control = new AbortController();
    const timer = setTimeout(() => control.abort(), WRITE_MS);

    try {
        const response = await fetch(`${API}${path}`, { ...init, signal: control.signal });
        if (!response.ok) {
            throw new Refused(response.status);
        }
        return await response.text();
    } finally {
        clearTimeout(timer);
    }
}

// Reads the places saved against a code
export async function readPlaces(signal: AbortSignal): Promise<SavedPlace[]> {
    const response = await fetch(`${API}/v1/places`, { signal, headers: codeHeader() });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Reads the places a half-typed address could be
export async function suggestPlaces(typed: string, signal: AbortSignal): Promise<Suggestion[]> {
    const query = new URLSearchParams({ q: typed });
    const response = await fetch(`${API}/v1/places/suggest?${query}`, { signal });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Sends one save and keeps a newly minted code
async function post<Reply extends { code: string }>(path: string, payload: object): Promise<Reply> {
    // A save while another mints the code waits to share it
    if (readCode() === null && minting !== null) await minting;

    const had = readCode();
    const saving = (async () => {
        const body = await send(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...codeHeader() },
            body: JSON.stringify(payload),
        });
        const saved: Reply = JSON.parse(body);
        if (had === null) writeCode(saved.code);
        return saved;
    })();
    if (had === null) {
        minting = saving.then(
            () => {},
            () => {},
        );
    }
    return saving;
}

// Removes one saved thing
async function removeAt(path: string) {
    try {
        await send(path, { method: 'DELETE', headers: codeHeader(), keepalive: true });
    } catch (error) {
        if (!(error instanceof Refused && error.status === 404)) throw error;
    }
}

// What a code holds
export async function countUnder(code: string) {
    const init = { headers: { 'X-Pace-Code': code } };
    const [places, trips] = await Promise.all(
        ['/v1/places', '/v1/trips'].map(async (path) => {
            const list: unknown[] = JSON.parse(await send(path, init));
            return list.length;
        }),
    );
    return { places, trips };
}

// Saves one place
export async function savePlace(
    label: string,
    address: string,
    spot: Suggestion | null,
): Promise<SavedPlace> {
    const saved = await post<{ code: string; place: SavedPlace }>('/v1/places', {
        label,
        address,
        ...(spot && { lat: spot.lat, lon: spot.lon }),
    });
    return saved.place;
}

// Removes one saved place
export async function removePlace(id: number) {
    await removeAt(`/v1/places/${id}`);
}

// The key a trip is kept under this visit
const tripKey = (origin: string, destination: string) => `${origin} to ${destination}`;

// Whether a trip was saved this visit
export function isKept(origin: string, destination: string) {
    return kept.has(tripKey(origin, destination));
}

// Learns which trips are already saved
export function readKept(): Promise<void> {
    const code = readCode();
    if (code === null) return Promise.resolve();

    keptRead ??= send('/v1/trips', { headers: { 'X-Pace-Code': code } }).then(
        (body) => {
            if (code !== readCode()) return;
            const trips: SavedTrip[] = JSON.parse(body);
            for (const trip of trips) kept.add(tripKey(trip.origin, trip.destination));
        },
        (error) => {
            console.error(error);
            keptRead = null;
        },
    );
    return keptRead;
}

// A removed trip stops counting as saved
export function forget(origin: string, destination: string) {
    kept.delete(tripKey(origin, destination));
}

// Saves one trip with where its ends are
export async function saveTrip(card: TripCard): Promise<SavedTrip> {
    const { origin, destination, origin_at, destination_at } = card;
    const saved = await post<{ code: string; trip: SavedTrip }>('/v1/trips', {
        origin,
        destination,
        origin_at,
        destination_at,
    });
    kept.add(tripKey(origin, destination));
    return saved.trip;
}

// Removes one saved trip
export async function removeTrip(id: number) {
    await removeAt(`/v1/trips/${id}`);
}

// Reads the plan for every trip saved against a code
export async function readBoard(signal: AbortSignal): Promise<Planned[]> {
    const response = await fetch(`${API}/v1/board`, { signal, headers: codeHeader() });
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

// Reads every line's state
export async function readTransit(signal: AbortSignal): Promise<Live> {
    const response = await fetch(`${API}/v1/transit`, { signal });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Reads how every line has run today
export async function readReadings(signal: AbortSignal): Promise<Readings> {
    const response = await fetch(`${API}/v1/readings`, { signal });
    if (!response.ok) {
        throw new Error(`Pace returned ${response.status}`);
    }
    return response.json();
}

// Plans a trip whose ends were picked
export async function plan(pick: Picked): Promise<Answer> {
    const response = await fetch(`${API}/v1/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...codeHeader() },
        body: JSON.stringify(pick),
        signal: AbortSignal.timeout(WRITE_MS),
    });
    if (response.status === 429) {
        const { detail } = await response.json();
        throw new Notice(detail);
    }
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
            headers: { 'Content-Type': 'application/json', ...codeHeader() },
            body: JSON.stringify({ query }),
            signal: control.signal,
        });

        if (response.status === 429) {
            const { detail } = await response.json();
            throw new Notice(detail);
        }
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

            // Any byte proves the stream is alive and restarts the timer
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
