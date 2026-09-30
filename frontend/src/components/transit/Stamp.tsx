import { ageOf } from '@/lib/status';
import { useNow } from '@/hooks/useNow';
import { LIVE } from '@/components/layout/tints';

interface StampProps {
    retrievedAt: string;
}

function Stamp({ retrievedAt }: StampProps) {
    const now = useNow();

    return (
        <span className="flex shrink-0 items-center gap-2 rounded-full border border-edge bg-bubble px-3.25 py-1.75">
            <span className={`size-1.25 rounded-full ${LIVE}`} />
            <span className="font-mono text-stamp text-hush uppercase">
                Live · {ageOf(retrievedAt, now)}
            </span>
        </span>
    );
}

export default Stamp;
