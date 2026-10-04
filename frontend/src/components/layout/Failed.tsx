import clsx from 'clsx';
import { RotateCw } from 'lucide-react';

interface FailedProps {
    said: string;
    retry: () => void;
    className?: string;
}

function Failed({ said, retry, className }: FailedProps) {
    return (
        <div role="alert" className={clsx('flex items-center gap-2 text-sm', className)}>
            <span className="text-red">{said}</span>
            <span className="text-ghost" aria-hidden="true">
                ·
            </span>
            <button
                type="button"
                onClick={retry}
                className="relative flex cursor-pointer items-center gap-1 text-cream transition-[scale] ease-out active:scale-97 pointer-coarse:after:absolute pointer-coarse:after:-inset-x-2 pointer-coarse:after:-inset-y-3"
            >
                <RotateCw size={13} strokeWidth={2.2} />
                Try again
            </button>
        </div>
    );
}

export default Failed;
