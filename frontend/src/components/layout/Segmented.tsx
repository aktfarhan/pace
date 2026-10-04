import clsx from 'clsx';
import { useGlide } from '@/hooks/useGlide';
import { GLIDE, RAISED, TRACK } from './tints';

const SEGMENT =
    'relative min-w-10 rounded-full px-3 py-1 text-center font-mono text-tag uppercase pointer-coarse:after:absolute pointer-coarse:after:inset-x-0 pointer-coarse:after:-inset-y-2.5';

interface SegmentedProps<Option extends string> {
    label: string;
    options: readonly Option[];
    value: Option;
    pick: (option: Option) => void;
}

function Segmented<Option extends string>({ label, options, value, pick }: SegmentedProps<Option>) {
    const { rowRef, glideRef } = useGlide(value, 2);

    return (
        <div
            ref={rowRef}
            role="group"
            aria-label={label}
            className={clsx(TRACK, 'relative flex shrink-0 gap-0.5 p-0.5')}
        >
            {options.map((one) => (
                <button
                    key={one}
                    type="button"
                    aria-pressed={one === value}
                    data-picked={one === value}
                    onClick={() => pick(one)}
                    className={clsx(
                        SEGMENT,
                        'cursor-pointer text-dim transition ease-out hover:text-soft active:scale-96',
                    )}
                >
                    {one}
                </button>
            ))}
            <div ref={glideRef} aria-hidden="true" className={`${GLIDE} flex gap-0.5 p-0.5`}>
                {options.map((one) => (
                    <span key={one} className={clsx(SEGMENT, RAISED, 'text-cream')}>
                        {one}
                    </span>
                ))}
            </div>
        </div>
    );
}

export default Segmented;
