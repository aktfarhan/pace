export const ZONE = 'America/New_York';

const PARTS = new Intl.DateTimeFormat('en-US', {
    timeZone: ZONE,
    hourCycle: 'h23',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
});

// A moment's date and time on Boston's clock
function partsOf(at: number) {
    const parts: Record<string, number> = {};
    for (const { type, value } of PARTS.formatToParts(at)) {
        if (type !== 'literal') parts[type] = Number(value);
    }
    return parts as Record<'year' | 'month' | 'day' | 'hour' | 'minute', number>;
}

// The hour it is in Boston
export function bostonHour(at: number) {
    return partsOf(at).hour;
}

// The date it is in Boston
export function bostonDate(at: number) {
    const { year, month, day } = partsOf(at);
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

// When Boston's clock reads an hour
export function bostonMoment(at: number, days: number, hour: number) {
    const { year, month, day } = partsOf(at);

    // The time wanted
    const wanted = Date.UTC(year, month - 1, day + days, hour);

    // Shift by what Boston's clock reads
    let guess = wanted;
    for (let tries = 0; tries < 2; tries += 1) {
        const shown = partsOf(guess);
        const read = Date.UTC(shown.year, shown.month - 1, shown.day, shown.hour);
        guess += wanted - read;
    }
    return guess;
}
