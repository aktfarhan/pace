import clsx from 'clsx';
import type { Level } from '@/types/answer';

// The pill each label wears
const PILLS: Record<Level, string> = {
    low: 'border-good/25 bg-good/10 text-good',
    mid: 'border-amber/25 bg-amber/10 text-amber',
    high: 'border-red-fill/25 bg-red-fill/10 text-red',
};

// The dot in front of it
const DOTS: Record<Level, string> = {
    low: 'bg-good',
    mid: 'bg-amber',
    high: 'bg-red',
};

const PILL = 'rounded-full border px-2.25 py-hair font-mono text-tag uppercase';

interface RiskProps {
    risk: Level | null;
}

function Risk({ risk }: RiskProps) {
    if (risk === null) {
        return <span className={clsx(PILL, 'border-line text-dim')}>Risk —</span>;
    }

    return (
        <span className={clsx(PILL, 'inline-flex items-center gap-1.5', PILLS[risk])}>
            <span className={clsx('size-1.5 rounded-full', DOTS[risk])} aria-hidden="true" />
            {risk} risk
        </span>
    );
}

export default Risk;
