import clsx from 'clsx';
import Drift from '@/components/transit/lines/Drift';
import { percentOf } from './figures';
import { useTicks } from '@/hooks/useTicks';
import { TICK } from '@/components/layout/tints';
import type { Figure } from './figures';
import type { Emphasis } from './useEmphasis';

const CHIP =
    'flex cursor-pointer items-center gap-1.5 rounded-chip border px-2 py-1 font-mono text-state uppercase transition ease-out active:scale-97 disabled:cursor-default';

interface LegendProps {
    figures: Figure[];
    picked: Emphasis['picked'];
    strengthOf: Emphasis['strengthOf'];
    light: Emphasis['light'];
    toggle: Emphasis['toggle'];
}

function Legend({ figures, picked, strengthOf, light, toggle }: LegendProps) {
    const { ticking, settle } = useTicks(figures.map(({ line, share }) => [line.id, share]));

    // Each chip's state
    const chips = figures.map((figure) => {
        const held = picked.has(figure.line.id);
        const empty = figure.share === null && !held;
        return { ...figure, held, empty, faded: strengthOf(figure.line.id) < 1 };
    });

    return (
        <div className="-ml-2.25 flex flex-wrap items-center gap-1.5">
            {chips.map(({ line, share, drift, held, empty, faded }) => (
                <button
                    key={line.id}
                    type="button"
                    aria-pressed={held}
                    disabled={empty}
                    title={empty ? 'No readings yet today' : undefined}
                    onClick={() => toggle(line.id)}
                    onPointerEnter={() => !empty && light(line.id)}
                    onPointerLeave={() => light(null)}
                    onFocus={({ target }) => target.matches(':focus-visible') && light(line.id)}
                    onBlur={() => light(null)}
                    className={clsx(
                        CHIP,
                        held ? 'border-edge bg-field' : 'border-transparent',
                        !held && !empty && 'hover:bg-field/60',
                        faded && 'opacity-30',
                    )}
                >
                    <span className={`${line.fill} size-1.5 shrink-0 rounded-full`} />
                    <span className={empty ? 'text-faint' : line.text}>{line.code}</span>
                    <span
                        key={share ?? 'none'}
                        onTransitionEnd={() => settle(line.id, share)}
                        className={clsx('text-soft tabular-nums', ticking(line.id, share) && TICK)}
                    >
                        {percentOf(share)}
                    </span>
                    <Drift points={drift} />
                </button>
            ))}
        </div>
    );
}

export default Legend;
