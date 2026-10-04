import clsx from 'clsx';
import { ageOf } from '@/lib/status';
import { STALE_MS } from '@/lib/poll';
import { useNow } from '@/hooks/useNow';
import Spin from '@/components/layout/Spin';
import { BEHIND, LIVE, STAMP } from '@/components/layout/tints';

interface RefreshProps {
    readAt: string;
    reading: boolean;
    refresh: () => void;
}

function Refresh({ readAt, reading, refresh }: RefreshProps) {
    const now = useNow();
    const stale = now - Date.parse(readAt) > STALE_MS;

    return (
        <button
            type="button"
            onClick={refresh}
            title="Re-plan every trip"
            aria-label={stale ? 'Trips are behind; re-plan every trip' : 'Re-plan every trip'}
            className={STAMP}
        >
            <span className={clsx('size-1.25 shrink-0 rounded-full', stale ? BEHIND : LIVE)} />
            <span className="font-mono text-stamp uppercase">
                {stale ? 'Last read' : 'Live'} · {ageOf(readAt, now)}
            </span>
            <Spin on={reading} />
        </button>
    );
}

export default Refresh;
