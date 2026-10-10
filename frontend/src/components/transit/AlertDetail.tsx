import clsx from 'clsx';
import { datesOf, sinceOf } from './feed';
import type { LineAlert } from '@/types/status';

interface AlertDetailProps {
    id: string;
    open: boolean;
    alerts: LineAlert[];
}

function AlertDetail({ id, open, alerts }: AlertDetailProps) {
    // Dates, time and place for the alerts
    const items = alerts.map((alert) => {
        const since = sinceOf(alert.since);
        const place = alert.where === null ? since : `${since} · ${alert.where}`;
        return { alert, said: alerts.length > 1 ? place : datesOf(alert.since, alert.until) };
    });

    return (
        <div
            id={id}
            inert={!open}
            className={clsx(
                'grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-opacity',
                open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0',
            )}
        >
            <div className="overflow-hidden pr-4 pl-16">
                <div className="flex flex-col gap-3 pb-4">
                    {items.map(({ alert, said }) => (
                        <div key={alert.alert_id}>
                            {said !== null && (
                                <span className="block pb-1.5 font-mono text-chip text-faint uppercase">
                                    {said}
                                </span>
                            )}
                            <p className="text-branch leading-relaxed text-pretty text-hush">
                                {alert.detail || 'No further detail from the MBTA.'}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default AlertDetail;
