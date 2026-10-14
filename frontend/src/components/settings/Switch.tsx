import clsx from 'clsx';

interface SwitchProps {
    on: boolean;
    label: string;
    described: string;
    flip: (on: boolean) => void;
}

function Switch({ on, label, described, flip }: SwitchProps) {
    return (
        <button
            type="button"
            role="switch"
            aria-checked={on}
            aria-label={label}
            aria-describedby={described}
            onClick={() => flip(!on)}
            className={clsx(
                'relative h-6 w-10 cursor-pointer rounded-full border transition duration-200 ease-out active:scale-97',
                on ? 'border-accent/60 bg-accent' : 'border-edge bg-field',
            )}
        >
            <span
                className={clsx(
                    'absolute top-0.5 left-0.5 size-4.5 rounded-full shadow-card transition duration-200 ease-in-out motion-reduce:transition-none',
                    on ? 'translate-x-4 bg-onaccent' : 'bg-hush',
                )}
            />
        </button>
    );
}

export default Switch;
