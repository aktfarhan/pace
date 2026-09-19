import clsx from 'clsx';
import type { Drawn } from '@/lib/lines';
import type { Emphasis } from '@/hooks/useEmphasis';

const CHIP =
    'flex cursor-pointer items-center gap-1.5 rounded-chip border px-2 py-1 font-mono text-state uppercase transition-opacity';

interface LegendProps {
    lines: readonly Drawn[];
    figures: Record<string, number | null>;
    picked: Emphasis['picked'];
    strengthOf: Emphasis['strengthOf'];
    light: Emphasis['light'];
    toggle: Emphasis['toggle'];
}

function Legend({ lines, figures, picked, strengthOf, light, toggle }: LegendProps) {
    return (
        <div className="flex flex-wrap items-center gap-1.5">
            {lines.map((line) => {
                const figure = figures[line.id];
                const held = picked.has(line.id);
                const faded = strengthOf(line.id) < 1;

                return (
                    <button
                        key={line.id}
                        type="button"
                        aria-pressed={held}
                        aria-label={`${line.label}, ${figure === null ? 'no readings' : `${figure} percent late`}`}
                        onClick={() => toggle(line.id)}
                        onPointerEnter={() => light(line.id)}
                        onPointerLeave={() => light(null)}
                        onFocus={() => light(line.id)}
                        onBlur={() => light(null)}
                        className={clsx(
                            CHIP,
                            held ? 'border-edge bg-field' : 'border-seam hover:border-edge',
                            faded && 'opacity-30',
                        )}
                    >
                        <span className={`${line.fill} size-1.5 shrink-0 rounded-full`} />
                        <span className={line.text}>{line.code}</span>
                        <span className="text-soft tabular-nums">
                            {figure === null ? '—' : `${figure}%`}
                        </span>
                    </button>
                );
            })}
        </div>
    );
}

export default Legend;
