import Alert from './Alert';
import type { Notice } from '@/types/transit';

interface NoticesProps {
    notices: Notice[];
    bare: boolean;
}

function Notices({ notices, bare }: NoticesProps) {
    if (notices.length === 0 && bare) return null;

    return (
        <section>
            <div className="flex items-baseline gap-2.5 px-0.5 pt-5 pb-3">
                <span className="text-headline whitespace-nowrap text-bright">Alerts</span>
                <span className="text-title text-ghost tabular-nums">{notices.length}</span>
            </div>
            {notices.length === 0 ? (
                <p className="text-branch text-ghost">Nothing reported on this line.</p>
            ) : (
                <div className="grid gap-2 xl:grid-cols-2">
                    {notices.map(({ lines, alert }) => (
                        <Alert key={alert.alert_id} lines={lines} alert={alert} />
                    ))}
                </div>
            )}
        </section>
    );
}

export default Notices;
