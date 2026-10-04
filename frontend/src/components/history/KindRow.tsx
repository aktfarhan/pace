import clsx from 'clsx';
import { FILLS, lookOf } from './tints';
import type { Kind } from '@/lib/insights';

const ROW =
    'flex w-full cursor-pointer items-center gap-2.5 rounded-row px-2 py-1 text-left transition ease-out hover:bg-field active:scale-98';

interface KindRowProps {
    kind: Kind;
    count: number;
    share: number;
    picked: boolean;
    pick: () => void;
}

function KindRow({ kind, count, share, picked, pick }: KindRowProps) {
    const look = lookOf(kind);

    return (
        <button
            type="button"
            aria-pressed={picked}
            onClick={pick}
            className={clsx(ROW, picked && 'bg-field ring-1 ring-edge')}
        >
            <span className={clsx('grid size-6 place-items-center rounded-mark', look.tile)}>
                <look.Icon size={12} strokeWidth={2} />
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-1.25">
                <span className="flex items-baseline justify-between gap-2">
                    <span className="text-row text-soft">{look.label}</span>
                    <span className="font-mono text-tag text-faint tabular-nums">{count}</span>
                </span>
                <span className="h-0.75 overflow-hidden rounded-full bg-line">
                    <span
                        className={clsx('block h-full rounded-full', FILLS[kind])}
                        style={{ width: `${share * 100}%` }}
                    />
                </span>
            </span>
        </button>
    );
}

export default KindRow;
