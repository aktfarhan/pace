import clsx from 'clsx';
import Mark from './Mark';
import { lookOf } from './tints';
import { fullClock } from '@/lib/trip';
import { entryKind } from '@/lib/insights';
import type { Entry } from '@/types/history';

const PILL = 'block rounded-full border px-2 py-0.75 font-mono text-tag whitespace-nowrap';

interface RowProps {
    entry: Entry;
}

function Row({ entry }: RowProps) {
    const look = lookOf(entryKind(entry));
    const said = entry.detail === '' ? look.label : `${look.label} · ${entry.detail}`;
    const chip =
        entry.chip === null ? null : <span className={clsx(PILL, look.pill)}>{entry.chip}</span>;

    return (
        <div className="flex items-center gap-3.5 px-4 py-3.25">
            <Mark Icon={look.Icon} tile={look.tile} />

            <div className="min-w-0 flex-1">
                <div className="truncate text-branch text-bright">{entry.query}</div>
                <div className="truncate text-xs text-faint">{said}</div>
                {chip !== null && <div className="mt-1.5 w-fit sm:hidden">{chip}</div>}
            </div>

            {chip !== null && <div className="hidden sm:block">{chip}</div>}

            <span className="w-14 shrink-0 text-right font-mono text-tag whitespace-nowrap text-faint sm:w-18">
                {fullClock(entry.at)}
            </span>
        </div>
    );
}

export default Row;
