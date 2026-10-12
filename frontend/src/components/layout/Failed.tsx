import clsx from 'clsx';
import TryAgain from './TryAgain';

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
            <TryAgain retry={retry} />
        </div>
    );
}

export default Failed;
