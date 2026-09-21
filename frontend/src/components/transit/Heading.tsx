import Range from './Range';
import { CHIP } from './tints';
import Branches from './Branches';
import type { Branching } from '@/types/transit';

interface HeadingProps {
    late: number;
    stretched: boolean;
    tight: boolean;
    span: number | null;
    readout: string | null;
    branching: Branching | null;
    select: (hours: number | null) => void;
}

function Heading({ late, stretched, tight, span, readout, branching, select }: HeadingProps) {
    return (
        <div className="flex items-center justify-between gap-3">
            <span className={`${CHIP} min-w-0 truncate text-hush`}>
                {tight
                    ? `${late}+ minutes late`
                    : `Arrivals over ${late} minutes late · rolling ${stretched ? 'window' : 'hour'}`}
            </span>
            <div className="flex shrink-0 items-center gap-1.5">
                <Range span={span} select={select} />
                {branching !== null && <Branches branching={branching} />}
                {readout !== null && (
                    <span className={`${CHIP} shrink-0 text-soft tabular-nums`}>{readout}</span>
                )}
            </div>
        </div>
    );
}

export default Heading;
