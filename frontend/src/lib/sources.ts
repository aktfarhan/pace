// What each kind of source is called
const NAMES = new Map([
    ['plan', 'MBTA trip planner'],
    ['alert', 'MBTA alerts'],
    ['schedule', 'MBTA timetable'],
    ['stop', 'MBTA stations'],
    ['route', 'MBTA routes'],
    ['street-cleaning', 'city street-cleaning rules'],
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
