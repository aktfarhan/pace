import clsx from 'clsx';
import { ArrowUp } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const CELL = 'col-start-1 row-start-1 transition-[opacity,filter] ease-out';

interface MarkProps {
    Icon: LucideIcon;
    tile: string;
}

function Mark({ Icon, tile }: MarkProps) {
    return (
        <span className={clsx('grid size-8.5 shrink-0 place-items-center rounded-mark', tile)}>
            <Icon
                size={15}
                strokeWidth={1.8}
                className={clsx(
                    CELL,
                    'group-hover:opacity-0 group-hover:blur-xs group-focus-visible:opacity-0 group-focus-visible:blur-xs',
                )}
            />
            <ArrowUp
                size={15}
                strokeWidth={2.4}
                className={clsx(
                    CELL,
                    'opacity-0 blur-xs group-hover:opacity-100 group-hover:blur-none group-focus-visible:opacity-100 group-focus-visible:blur-none',
                )}
            />
        </span>
    );
}

export default Mark;
