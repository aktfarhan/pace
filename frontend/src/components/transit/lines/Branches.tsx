import Picker from './Picker';
import { rowsOf } from './standing';
import Segmented from '@/components/layout/Segmented';
import type { Branching } from '@/types/transit';

const ROOM = 5;

interface BranchesProps {
    branching: Branching;
}

function Branches({ branching }: BranchesProps) {
    const { line, branches, pick } = branching;
    if (branches.length > ROOM) return <Picker branching={branching} />;

    const { rows, shown } = rowsOf(branching);

    return (
        <>
            <div className="@max-lg:hidden">
                <Segmented
                    label={`${line.label} branch`}
                    options={rows.map((row) => row.name)}
                    value={shown.name}
                    tint={line.text}
                    pick={(name) => pick(rows.find((row) => row.name === name)?.id ?? null)}
                />
            </div>
            <div className="hidden @max-lg:block">
                <Picker branching={branching} />
            </div>
        </>
    );
}

export default Branches;
