import clsx from 'clsx';
import Alert from './Alert';
import SectionHeading from '@/components/layout/SectionHeading';
import type { Notice } from '@/types/transit';

interface AlertGroupProps {
    name: string;
    notices: Notice[];
    panel: string;
    searching: boolean;
}

function AlertGroup({ name, notices, panel, searching }: AlertGroupProps) {
    return (
        <div>
            <SectionHeading label={name} count={notices.length} level={3} />
            <div
                className={clsx(
                    'divide-y divide-seam overflow-hidden rounded-tile border shadow-card',
                    panel,
                )}
            >
                {notices.map(({ lines, alert }) => (
                    <Alert key={alert.alert_id} lines={lines} alert={alert} searching={searching} />
                ))}
            </div>
        </div>
    );
}

export default AlertGroup;
