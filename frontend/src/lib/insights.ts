import type { Entry } from '@/types/history';
import type { Intent } from '@/types/answer';

// What a question counts as
export type Kind = Intent | 'refused';

// The intent one question counts as
export function entryKind(entry: Entry): Kind {
    return entry.refused ? 'refused' : entry.intent;
}

// A question folded for comparing
export function foldOf(query: string) {
    return query
        .toLowerCase()
        .replace(/[?.!\s]+$/, '')
        .trim()
        .replace(/\s+/g, ' ');
}

// The questions most repeated
export function mostAsked(entries: Entry[], keep: number) {
    const seen = new Map<string, { query: string; count: number }>();
    for (const entry of entries) {
        if (entry.refused) continue;
        const key = foldOf(entry.query);
        const one = seen.get(key);
        if (one === undefined) {
            seen.set(key, { query: entry.query.trim(), count: 1 });
        } else {
            one.count += 1;
        }
    }
    return [...seen.values()]
        .filter((one) => one.count > 1)
        .sort((a, b) => b.count - a.count)
        .slice(0, keep);
}
