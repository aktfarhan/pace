import clsx from 'clsx';
import Drift from './Drift';
import type { Figure } from './figures';
import type { Emphasis } from '@/hooks/useEmphasis';

const CHIP =
    'flex cursor-pointer items-center gap-1.5 rounded-chip border px-2 py-1 font-mono text-state uppercase transition-opacity';

interface LegendProps {
    figures: Figure[];
    picked: Emphasis['picked'];
    strengthOf: Emphasis['strengthOf'];
    light: Emphasis['light'];
    toggle: Emphasis['toggle'];
}

function Legend({ figures, picked, strengthOf, light, toggle }: LegendProps) {
    return (
        <div className="flex flex-wrap items-center gap-1.5">
            {figures.map(({ line, share, drift }) => {
                const held = picked.has(line.id);
                const faded = strengthOf(line.id) < 1;

                return (
                    <button
                        key={line.id}
                        type="button"
                        aria-pressed={held}
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
                            {share === null ? '—' : `${share}%`}
                        </span>
                        <Drift points={drift} />
                    </button>
                );
            })}
        </div>
    );
}

export default Legend;
