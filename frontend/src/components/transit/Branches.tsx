import clsx from 'clsx';
import Picker from './Picker';
import { EVERY, SEGMENT, SHELL } from './tints';
import type { Branching } from '@/types/transit';

const ROOM = 5;

interface BranchesProps {
    branching: Branching;
}

function Branches({ branching }: BranchesProps) {
    const { line, branches, branch, pick } = branching;
    if (branches.length > ROOM) return <Picker branching={branching} />;

    return (
        <div className={clsx(SHELL, 'flex shrink-0 gap-0.5 p-0.5')}>
            <button
                type="button"
                aria-pressed={branch === null}
                onClick={() => pick(null)}
                className={clsx(SEGMENT, branch === null ? line.chip : 'text-dim')}
            >
                {EVERY}
            </button>
            {branches.map(({ id, name }) => (
                <button
                    key={id}
                    type="button"
                    aria-pressed={branch === id}
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
