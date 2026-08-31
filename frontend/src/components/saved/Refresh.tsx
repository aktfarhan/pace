import { ageOf } from '@/lib/status';
import { useNow } from '@/hooks/useNow';
import { RotateCw } from 'lucide-react';

const PILL =
    'flex shrink-0 cursor-pointer items-center gap-2 rounded-full border border-edge bg-bubble px-3.25 py-1.75 text-hush transition-colors hover:border-ghost hover:bg-line hover:text-cream';

interface RefreshProps {
    readAt: string;
    reading: boolean;
    refresh: () => void;
}

function Refresh({ readAt, reading, refresh }: RefreshProps) {
    const now = useNow();

    return (
        <button
            type="button"
            onClick={refresh}
            title="Re-plan every trip"
            aria-label="Re-plan every trip"
            className={PILL}
        >
            <span className="size-1.25 shrink-0 animate-beacon rounded-full bg-good shadow-glow" />
            <span className="font-mono text-stamp uppercase">
                {readAt === '' ? '—' : ageOf(readAt, now)}
            </span>
            <RotateCw
                size={12}
                strokeWidth={2.4}
                className={reading ? 'animate-spin text-quiet' : 'text-quiet'}
                aria-hidden="true"
            />
        </button>
    );
}

export default Refresh;
