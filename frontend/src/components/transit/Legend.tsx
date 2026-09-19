import type { Drawn } from '@/lib/lines';

const CHIP =
    'flex items-center gap-1.5 rounded-chip border border-seam px-2 py-1 font-mono text-state uppercase';

interface LegendProps {
    lines: readonly Drawn[];
    figures: Record<string, number | null>;
}

function Legend({ lines, figures }: LegendProps) {
    return (
        <div className="flex flex-wrap items-center gap-1.5">
            {lines.map((line) => {
                const figure = figures[line.id];

                return (
                    <span key={line.id} className={CHIP}>
                        <span className={`${line.fill} size-1.5 shrink-0 rounded-full`} />
                        <span className={line.text}>{line.code}</span>
                        <span className="text-soft tabular-nums">
                            {figure === null ? '—' : `${figure}%`}
                        </span>
                    </span>
                );
            })}
        </div>
    );
}

export default Legend;
