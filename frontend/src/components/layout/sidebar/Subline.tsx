import { useNow } from '@/hooks/useNow';
import { sublineOf } from '@/lib/status';
import type { SystemStatus } from '@/types/status';

interface SublineProps {
    status: SystemStatus;
}

function Subline({ status }: SublineProps) {
    const now = useNow();

    return (
        <span className="truncate pl-4.5 font-mono text-subline text-ghost uppercase">
            {sublineOf(status, now)}
        </span>
    );
}

export default Subline;
