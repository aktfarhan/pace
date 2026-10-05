import clsx from 'clsx';
import { PRESETS } from './kinds';

const PRESET =
    'flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-row transition ease-out active:scale-97';

interface PresetsProps {
    label: string;
    pick: (name: string) => void;
}

function Presets({ label, pick }: PresetsProps) {
    return (
        <div role="group" aria-label="Kinds of place" className="flex flex-wrap gap-1.5">
            {PRESETS.map(({ name, Icon }) => (
                <button
                    key={name}
                    type="button"
                    aria-pressed={label === name}
                    onClick={() => pick(name)}
                    className={clsx(
                        PRESET,
                        label === name
                            ? 'border-accent/30 bg-accent/10 text-accent'
                            : 'border-edge bg-field text-soft hover:bg-bubble hover:text-cream',
                    )}
                >
                    <Icon size={13} strokeWidth={2} />
                    {name}
                </button>
            ))}
        </div>
    );
}

export default Presets;
