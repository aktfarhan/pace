import type { Chip, State, AlertedLine, LineStatus, SystemStatus } from '@/types/status';

// A group of lines under one heading
interface Section {
    heading: string;
    lines: LineStatus[];
}

// Worst first
const ORDER: State[] = ['severe', 'disrupted', 'notice', 'clear'];

// A group's heading when its lines disagree on the effect
const STATE_HEADINGS: Record<State, string> = {
    severe: 'Not running',
    disrupted: 'Disrupted',
    notice: 'Notices',
    clear: 'Running normally',
};

// A group's heading when its lines share one effect
const EFFECT_HEADINGS: Record<string, string> = {
    SUSPENSION: 'Suspended',
    NO_SERVICE: 'No service',
    CANCELLATION: 'Cancelled',
    SHUTTLE: 'Planned diversion',
    DETOUR: 'Detours',
    DELAY: 'Delayed',
    TRACK_CHANGE: 'Service changes',
    SERVICE_CHANGE: 'Service changes',
    STOP_MOVE: 'Service changes',
    STOP_MOVED: 'Service changes',
};

// The sentence one affected line gets
const HEADLINES: Record<string, (line: string) => string> = {
    SUSPENSION: (line) => `${line} suspended`,
    NO_SERVICE: (line) => `No service on ${line}`,
    CANCELLATION: (line) => `${line} cancelled`,
    SHUTTLE: (line) => `Shuttles on ${line}`,
    DETOUR: (line) => `${line} detoured`,
    DELAY: (line) => `${line} delayed`,
    TRACK_CHANGE: (line) => `Track change on ${line}`,
    SERVICE_CHANGE: (line) => `Service change on ${line}`,
    STOP_MOVE: (line) => `Stop moved on ${line}`,
    STOP_MOVED: (line) => `Stop moved on ${line}`,
};

// The word an effect goes by on a card
const EFFECT_WORDS: Record<string, string> = {
    SUSPENSION: 'Suspended',
    NO_SERVICE: 'No service',
    CANCELLATION: 'Cancelled',
    SHUTTLE: 'Shuttles',
    DETOUR: 'Detour',
    DELAY: 'Delayed',
    TRACK_CHANGE: 'Track change',
    SERVICE_CHANGE: 'Service change',
    STOP_MOVE: 'Stop moved',
    STOP_MOVED: 'Stop moved',
};

// The effects that change how a train runs
const SERVICE_EFFECTS = new Set(Object.keys(EFFECT_WORDS));

// The only line whose branches the feed names separately
export const BRANCHED = 'Green';

// Whether the train is running, whatever the alert is about
export function running(line: LineStatus) {
    return line.state === 'clear' || !SERVICE_EFFECTS.has(line.effect);
}

// How many lines are running normally
export function runningCount(lines: LineStatus[]) {
    let count = 0;
    for (const line of lines) {
        if (running(line)) {
            count += 1;
        }
    }
    return count;
}

// An unmapped enum, spelled out
function spellOut(value: string) {
    const words = value.replaceAll('_', ' ').toLowerCase();
    return words.charAt(0).toUpperCase() + words.slice(1);
}

export function effectWord(effect: string) {
    return EFFECT_WORDS[effect] ?? spellOut(effect);
}

// Splits the lines into the sections the sidebar stacks
export function sectionsOf(lines: LineStatus[]) {
    const sections: Section[] = [];

    for (const state of ORDER) {
        // The lines for this section
        const group = [];
        for (const line of lines) {
            const belongsIn = running(line) ? 'clear' : line.state;
            if (belongsIn === state) {
                group.push(line);
            }
        }

        if (group.length === 0) {
            continue;
        }

        // Running lines always get the same heading
        if (state === 'clear') {
            sections.push({ heading: STATE_HEADINGS.clear, lines: group });
            continue;
        }

        // The headings these lines want
        const headings: string[] = [];
        for (const line of group) {
            if (line.state === 'clear') {
                continue;
            }
            const named = EFFECT_HEADINGS[line.effect] ?? STATE_HEADINGS[state];
            if (!headings.includes(named)) {
                headings.push(named);
            }
        }

        // All the same heading, or a general one
        const heading = headings.length === 1 ? headings[0] : STATE_HEADINGS[state];
        sections.push({ heading, lines: group });
    }

    return sections;
}

// The lines that are not running
function hitLines(status: SystemStatus) {
    const hit: AlertedLine[] = [];
    for (const line of status.lines) {
        if (line.effect !== null && !running(line)) {
            hit.push(line);
        }
    }
    return hit;
}

// The headline at the top of the sidebar
export function headlineOf(status: SystemStatus) {
    if (!status.ok) {
        return 'Status unavailable';
    }

    const hit = hitLines(status);

    if (hit.length === 0) {
        return `All ${status.lines.length} lines on time`;
    }

    // One line, so name it and say what happened
    if (hit.length === 1) {
        const say = HEADLINES[hit[0].effect];
        if (say !== undefined) {
            return say(hit[0].line_name);
        }
        return `${hit[0].line_name}: ${effectWord(hit[0].effect).toLowerCase()}`;
    }
    return `${hit.length} lines disrupted`;
}

// How long ago the reading was taken
function ageOf(retrievedAt: string, now: number) {
    const seconds = Math.max(0, Math.round((now - Date.parse(retrievedAt)) / 1000));
    if (seconds < 60) {
        return `${seconds}s ago`;
    }
    return `${Math.floor(seconds / 60)}m ago`;
}

// The caption under the headline
export function sublineOf(status: SystemStatus, now: number) {
    if (!status.ok) {
        return 'Feed unreachable';
    }

    const age = `Updated ${ageOf(status.retrieved_at, now)}`;
    const ok = runningCount(status.lines);

    if (ok === status.lines.length) {
        return age;
    }
    if (ok === status.lines.length - 1) {
        return `${ok} other lines on time · ${age}`;
    }
    return `${ok} lines on time · ${age}`;
}

// No direction on an alert means it covers every direction
function bothDirections(line: LineStatus) {
    return line.directions.length !== 1;
}

// The two facts under a card's title row
export function chipsOf(line: LineStatus): Chip[] {
    if (running(line)) {
        return [
            { text: 'Typical —', tone: 'blank' },
            { text: 'Both directions', tone: 'quiet' },
        ];
    }

    const scope: Chip = {
        text: bothDirections(line) ? 'Both directions' : 'One direction',
        tone: 'read',
    };
    if (line.alert_count > 1) {
        return [scope, { text: `${line.alert_count} alerts`, tone: 'quiet' }];
    }
    return [scope, { text: 'Typical —', tone: 'blank' }];
}
