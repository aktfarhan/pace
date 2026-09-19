import Range from './Range';
import { CHIP } from './tints';

interface HeadingProps {
    late: number;
    stretched: boolean;
    tight: boolean;
    span: number | null;
    select: (hours: number | null) => void;
}

function Heading({ late, stretched, tight, span, select }: HeadingProps) {
    return (
        <div className="flex items-center justify-between gap-3">
            <span className={`${CHIP} min-w-0 truncate text-hush`}>
                {tight
                    ? `${late}+ minutes late`
                    : `Arrivals over ${late} minutes late · rolling ${stretched ? 'window' : 'hour'}`}
            </span>
            <Range span={span} select={select} />
        </div>
    );
}

export default Heading;
