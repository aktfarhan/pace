import Range from './Range';
import { memo } from 'react';
import Explain from './Explain';
import Branches from './Branches';
import type { Branching } from '@/types/transit';

interface HeadingProps {
    late: number;
    rolling: number;
    span: number | null;
    branching: Branching | null;
    select: (hours: number | null) => void;
}

function Heading({ late, rolling, span, branching, select }: HeadingProps) {
    return (
        <div className="@container relative flex min-h-6.75 flex-wrap items-center gap-x-3 gap-y-2">
            <div className="flex items-center gap-1">
                <h2 className="text-title text-bright">Late arrivals</h2>
                <Explain late={late} rolling={rolling} />
            </div>
            <div className="ml-auto flex min-w-0 gap-1.5">
                <Range span={span} select={select} />
                {branching !== null && <Branches branching={branching} />}
            </div>
        </div>
    );
}

export default memo(Heading);
