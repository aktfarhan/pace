import clsx from 'clsx';
import { BADGES } from './tints';
import { effectWord } from '@/lib/status';
import type { AlertedLine } from '@/types/status';

interface BranchesProps {
    line: AlertedLine;
}

// Every branch the Green Line splits into
const GREEN_BRANCHES = [
    { route_id: 'Green-B', name: 'Green Line B' },
    { route_id: 'Green-C', name: 'Green Line C' },
    { route_id: 'Green-D', name: 'Green Line D' },
    { route_id: 'Green-E', name: 'Green Line E' },
];

function Branches({ line }: BranchesProps) {
    const hit = line.branch_ids;

    // Check if the branches are ok
    let ok = 0;
    for (const branch of GREEN_BRANCHES) {
        if (!hit.includes(branch.route_id)) {
            ok += 1;
        }
    }

    return (
        <div className="flex flex-col gap-2.25 rounded-tile border border-seam bg-panel px-3.5 py-3.25">
            <div className="flex items-center gap-2.75">
                <span
                    className={clsx(
                        'shrink-0 rounded-chip border px-2 py-hair font-mono text-badge uppercase',
                        BADGES[line.line_id],
                    )}
                >
                    {line.badge_text}
                </span>
                <span className="min-w-0 flex-1 truncate text-base font-strong text-bright">
                    Four branches
                </span>
                <span className="shrink-0 font-mono text-state text-hush uppercase">
                    {ok} of {GREEN_BRANCHES.length} ok
                </span>
            </div>

            <div className="flex flex-col">
                {GREEN_BRANCHES.map((branch, index) => {
                    const affected = hit.includes(branch.route_id);
                    return (
                        <div
                            key={branch.route_id}
                            className={clsx(
                                'flex items-center gap-2.5 py-2',
                                index > 0 && 'border-t border-ink',
                            )}
                        >
                            <span
                                className={clsx(
                                    'size-2 shrink-0 rounded-full',
                                    affected ? 'bg-amber shadow-pulse' : 'bg-good shadow-glow',
                                )}
                                aria-hidden="true"
                            />
                            <span className="min-w-0 flex-1 truncate text-branch text-soft">
                                {branch.name}
                            </span>
                            <span
                                className={clsx(
                                    'shrink-0 font-mono text-state uppercase',
                                    affected ? 'text-amber' : 'text-steady',
                                )}
                            >
                                {affected ? effectWord(line.effect) : 'On time'}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default Branches;
