// The sources Settings lists
export const PLANNER = 'MBTA trip planner';
export const ALERTS = 'MBTA alerts';
export const TIMETABLE = 'MBTA timetable';

// What each kind of source is called
const NAMES = new Map([
    ['plan', PLANNER],
    ['alert', ALERTS],
    ['schedule', TIMETABLE],
    ['stop', 'MBTA stations'],
    ['route', 'MBTA routes'],
]);

// The sources an answer drew on
export function sourcesOf(ids: string[]) {
    const names = new Set<string>();
    for (const id of ids) {
        const name = NAMES.get(id.split(':')[0]);
        if (name !== undefined) names.add(name);
    }
    return [...names];
}
