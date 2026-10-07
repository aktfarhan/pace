import clsx from 'clsx';
import { datesOf } from './feed';
import type { LineAlert } from '@/types/status';

interface AlertDetailProps {
    id: string;
    open: boolean;
    alert: LineAlert;
}

function AlertDetail({ id, open, alert }: AlertDetailProps) {
    const dates = datesOf(alert.since, alert.until);

    return (
        <div
            id={id}
            inert={!open}
            className={clsx(
                'grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-opacity',
                open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0',
            )}
        >
            <div className="overflow-hidden px-4">
                <div className="pb-4">
                    {dates !== null && (
                        <span className="block pb-1.5 font-mono text-chip text-faint uppercase">
                            {dates}
                        </span>
                    )}
                    <p className="text-branch leading-relaxed text-pretty text-hush">
                        {alert.detail === '' ? 'No further detail from the MBTA.' : alert.detail}
                    </p>
                </div>
            </div>
        </div>
    );
}

export default AlertDetail;
