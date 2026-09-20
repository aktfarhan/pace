import Drift from './Drift';
import type { Figure } from './figures';

const BOX =
    'flex w-fit items-center gap-1.5 rounded-chip border border-seam px-2 py-1 font-mono text-state uppercase';

interface FocusProps {
    figure: Figure;
}

function Focus({ figure }: FocusProps) {
    const { line, share, drift } = figure;

    return (
        <span className={BOX}>
            <span className={`${line.fill} h-0.5 w-3.5 shrink-0 rounded-full`} />
            <span className="text-ghost">today</span>
            <span className="text-soft tabular-nums">
                {share === null ? 'no readings' : `${share}%`}
            </span>
            <Drift points={drift} />
        </span>
    );
}

export default Focus;
