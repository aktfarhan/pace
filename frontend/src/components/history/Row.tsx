import clsx from 'clsx';
import { fullClock } from '@/lib/trip';
import { KINDS, REFUSAL } from './tints';
import type { Entry } from '@/types/history';

const PILL =
    'shrink-0 rounded-full border px-2 py-0.75 font-mono text-tag whitespace-nowrap uppercase';

interface RowProps {
    entry: Entry;
}

function Row({ entry }: RowProps) {
    const kind = entry.refused ? REFUSAL : KINDS[entry.intent];
    const said = entry.detail === '' ? kind.label : `${kind.label} · ${entry.detail}`;

    return (
        <div className="flex items-center gap-3 px-3.5 py-3.25">
            <span
                className={clsx(
                    'grid size-8.5 shrink-0 place-items-center rounded-mark',
                    kind.tile,
                )}
            >
                <kind.Icon size={15} strokeWidth={1.8} aria-hidden="true" />
            </span>

            <div className="min-w-0 flex-1">
                <div className="truncate text-branch text-bright">{entry.query}</div>
                <div className="truncate text-xs text-faint">{said}</div>
            </div>

            {entry.chip !== null && <span className={clsx(PILL, kind.pill)}>{entry.chip}</span>}

            <span className="w-13 shrink-0 text-right font-mono text-tag text-ghost">
                {fullClock(entry.at)}
            </span>
        </div>
    );
}

export default Row;
