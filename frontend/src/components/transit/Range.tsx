import clsx from 'clsx';
import { SEGMENT, SHELL } from './tints';

// The stretches of the day for the main chart
const SPANS: { label: string; hours: number | null }[] = [
    { label: 'Day', hours: null },
    { label: '6h', hours: 6 },
    { label: '3h', hours: 3 },
];

interface RangeProps {
    span: number | null;
    select: (hours: number | null) => void;
}

function Range({ span, select }: RangeProps) {
    return (
        <div className={clsx(SHELL, 'flex shrink-0 gap-0.5 p-0.5')}>
            {SPANS.map(({ label, hours }) => (
                <button
                    key={label}
                    type="button"
                    onClick={() => select(hours)}
                    className={clsx(SEGMENT, span === hours ? 'bg-field text-soft' : 'text-dim')}
                >
                    {label}
                </button>
            ))}
        </div>
    );
}

export default Range;
