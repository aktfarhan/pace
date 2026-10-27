import type { SavedPlace } from '@/types/place';

// A letter or digit next to a name makes it part of a longer word
const WORD_CHAR = '[\\p{L}\\p{N}_]';

// The places the pattern was last built for
let builtFor: SavedPlace[] | null = null;
let built: RegExp | null = null;

// A name in the form matching compares
const keyOf = (text: string) => text.trim().toLowerCase().replace(/\s+/g, ' ');

// Finds any saved name as whole words
function patternFor(places: SavedPlace[]) {
    if (places === builtFor) return built;
    const names = [...new Set(places.map((place) => keyOf(place.label)).filter(Boolean))];

    // Longest names first
    names.sort((one, other) => other.length - one.length);
    const words = names.map((name) =>
        name.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&').replace(/ /g, '\\s+'),
    );

    builtFor = places;
    built =
        words.length === 0
            ? null
            : new RegExp(`(?<!${WORD_CHAR})(?:${words.join('|')})(?!${WORD_CHAR})`, 'giu');
    return built;
}

// The saved places a question names
export function placesNamed(text: string, places: SavedPlace[]) {
    const pattern = patternFor(places);
    if (pattern === null) return [];
    const found = new Set<SavedPlace>();
    for (const hit of text.matchAll(pattern)) {
        const place = places.find((one) => keyOf(one.label) === keyOf(hit[0]));
        if (place !== undefined) found.add(place);
    }
    return [...found];
}
