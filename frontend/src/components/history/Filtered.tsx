import { X } from 'lucide-react';
import { lookOf } from './tints';
import type { Kind } from '@/lib/insights';

interface FilteredProps {
    kind: Kind;
    clear: () => void;
}

function Filtered({ kind, clear }: FilteredProps) {
    const label = lookOf(kind).label;

    return (
        <button
            type="button"
            onClick={clear}
            aria-label={`Clear ${label} filter`}
            className="relative flex w-fit cursor-pointer items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 py-1 pr-2 pl-3 font-mono text-chip text-accent uppercase transition ease-out hover:bg-accent/15 active:scale-96 starting:scale-97 starting:opacity-0 motion-reduce:starting:scale-100 pointer-coarse:after:absolute pointer-coarse:after:inset-x-0 pointer-coarse:after:-inset-y-2.5"
        >
            Showing {label}
            <X size={11} strokeWidth={2.4} />
        </button>
    );
}

export default Filtered;
