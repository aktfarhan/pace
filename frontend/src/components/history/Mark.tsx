import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';

interface MarkProps {
    Icon: LucideIcon;
    tile: string;
}

function Mark({ Icon, tile }: MarkProps) {
    return (
        <span className={clsx('grid size-8.5 shrink-0 place-items-center rounded-mark', tile)}>
            <Icon size={15} strokeWidth={1.8} />
        </span>
    );
}

export default Mark;
