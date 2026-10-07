import clsx from 'clsx';
import { stretchOf } from './feed';

interface StretchProps {
    since: string | null;
    until: string | null;
    slowing: boolean;
}

function Stretch({ since, until, slowing }: StretchProps) {
    const stretch = stretchOf(since, until);

    // An empty slot keeps the pills lined up
    if (stretch === null) return <span className="hidden w-24 lg:block" />;

    return (
        <span className="hidden w-24 flex-col gap-1.5 lg:flex">
            <span className="font-mono text-chip text-faint uppercase">{stretch.label}</span>
            {stretch.progress !== null && (
                <span className="h-0.75 rounded-full bg-line">
                    <span
                        className={clsx(
                            'block h-full rounded-full',
                            slowing ? 'bg-amber/70' : 'bg-quiet/60',
                        )}
                        style={{ width: `${Math.round(stretch.progress * 100)}%` }}
                    />
                </span>
            )}
        </span>
    );
}

export default Stretch;
