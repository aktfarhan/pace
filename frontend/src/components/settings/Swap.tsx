import clsx from 'clsx';
import { TICK } from '@/components/layout/tints';
import type { ReactNode } from 'react';

interface SwapProps {
    on: string;
    className?: string;
    children: ReactNode;
}

function Swap({ on, className, children }: SwapProps) {
    return (
        <span key={on} className={clsx(TICK, className)}>
            {children}
        </span>
    );
}

export default Swap;
