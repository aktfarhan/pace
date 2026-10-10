import clsx from 'clsx';
import { kindOf } from './feed';
import type { Notice } from '@/types/transit';

const CHIP =
    'flex cursor-pointer items-center gap-1.5 rounded-full border px-2.75 py-1 font-mono text-chip uppercase transition ease-out active:scale-96';

interface KindFilterProps {
    notices: Notice[];
    kind: string | null;
    pick: (kind: string | null) => void;
}

function KindFilter({ notices, kind, pick }: KindFilterProps) {
    // Each kind in the list, with how many alerts it has
    const counts = new Map<string, ReturnType<typeof kindOf> & { count: number }>();
    for (const one of notices) {
        const found = kindOf(one.alert.effect);
        const seen = counts.get(found.name);
        if (seen === undefined) counts.set(found.name, { ...found, count: 1 });
        else seen.count += 1;
    }

    // Most common first
    const kinds = [...counts.values()].sort((a, b) => b.count - a.count);
    if (kinds.length < 2) return null;

    return (
        <div className="flex flex-wrap gap-1.5 px-1 pb-1">
            {kinds.map((one) => (
                <button
                    key={one.name}
                    type="button"
                    aria-pressed={kind === one.name}
                    onClick={() => pick(kind === one.name ? null : one.name)}
                    className={clsx(
                        CHIP,
                        kind === one.name
                            ? 'border-accent/30 bg-accent/10 text-accent'
                            : 'border-seam text-dim hover:border-edge hover:text-soft',
                    )}
                >
                    <one.Icon size={11} strokeWidth={2} />
                    {one.name}
                    <span className="tabular-nums opacity-70">{one.count}</span>
                </button>
            ))}
        </div>
    );
}

export default KindFilter;
