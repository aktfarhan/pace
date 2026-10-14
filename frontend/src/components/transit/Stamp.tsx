import clsx from 'clsx';
import { ageOf } from '@/lib/status';
import { STALE_MS } from '@/lib/poll';
import { useNow } from '@/hooks/useNow';
import { BEHIND, LIVE, STAMP } from '@/components/layout/tints';
import type { SystemStatus } from '@/types/status';

interface StampProps {
    status: SystemStatus;
    refresh: () => void;
}

function Stamp({ status, refresh }: StampProps) {
    const now = useNow();
    const { retrieved_at: retrievedAt, ok } = status;

    // An unreachable feed counts as behind
    const stale = !ok || now - Date.parse(retrievedAt) > STALE_MS;

    // The stamp's words
    const said = ok
        ? `${stale ? 'Last read' : 'Live'} · ${ageOf(retrievedAt, now)}`
        : 'Feed unreachable';

    return (
        <button type="button" onClick={refresh} title="Read the latest now" className={STAMP}>
            <span className={clsx('size-1.25 rounded-full', stale ? BEHIND : LIVE)} />
            <span className="font-mono text-stamp uppercase">{said}</span>
        </button>
    );
}

export default Stamp;
