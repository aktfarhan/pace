import clsx from 'clsx';
import { EVERY, SEGMENT, SHELL } from './tints';
import type { Branching } from '@/types/transit';

const ROOM = 5;

interface BranchesProps {
    branching: Branching;
}

function Branches({ branching }: BranchesProps) {
    const { line, branches, branch, pick } = branching;
    if (branches.length > ROOM) return null;

    return (
        <div className={clsx(SHELL, 'flex shrink-0 gap-0.5 p-0.5')}>
            <button
                type="button"
                onClick={() => pick(null)}
                className={clsx(SEGMENT, branch === null ? line.chip : 'text-dim')}
            >
                {EVERY}
            </button>
            {branches.map(({ id, name }) => (
                <button
                    key={id}
                    type="button"
                    onClick={() => pick(id)}
                    className={clsx(SEGMENT, branch === id ? line.chip : 'text-dim')}
                >
                    {name}
                </button>
            ))}
        </div>
    );
}

export default Branches;
