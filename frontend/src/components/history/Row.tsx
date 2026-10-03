import clsx from 'clsx';
import Mark from './Mark';
import { lookOf } from './tints';
import { fullClock } from '@/lib/trip';
import { entryKind } from '@/lib/insights';
import type { Entry } from '@/types/history';

const PILL = 'block rounded-full border px-2 py-0.75 font-mono text-tag whitespace-nowrap';

interface RowProps {
    entry: Entry;
    ask: (query: string) => void;
}

function Row({ entry, ask }: RowProps) {
    const look = lookOf(entryKind(entry));
    const said = entry.detail === '' ? look.label : `${look.label} · ${entry.detail}`;
    const chip =
        entry.chip === null ? null : <span className={clsx(PILL, look.pill)}>{entry.chip}</span>;

    return (
        <button
            type="button"
            onClick={() => ask(entry.query)}
            className="group flex w-full cursor-pointer items-center gap-3.5 px-4 py-3.25 text-left transition-colors ease-out hover:bg-field/70 focus-visible:-outline-offset-2 active:bg-field"
        >
            <span className="sr-only">Ask again: </span>
            <Mark Icon={look.Icon} tile={look.tile} />

            <span className="min-w-0 flex-1">
                <span className="block truncate text-branch text-bright">{entry.query}</span>
                <span className="block truncate text-xs text-faint">{said}</span>
                {chip !== null && <span className="mt-1.5 block w-fit sm:hidden">{chip}</span>}
            </span>

            {chip !== null && <span className="hidden sm:block">{chip}</span>}

            <span className="w-14 shrink-0 text-right font-mono text-tag whitespace-nowrap text-faint sm:w-18">
                {fullClock(entry.at)}
            </span>
        </button>
    );
}

export default Row;
