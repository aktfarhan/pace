import { useState } from 'react';
import { useNow } from '@/hooks/useNow';
import { TICK } from '@/components/layout/tints';
import type { Stage } from '@/types/answer';

const LABELS: Record<Stage, string> = {
    classify: 'Reading the question',
    retrieve: 'Searching the sources',
    plan: 'Planning the trip',
    alerts: 'Checking alerts',
    departures: 'Checking departures',
    generate: 'Writing the answer',
};

interface ThinkingProps {
    stage: Stage | null;
}

function Thinking({ stage }: ThinkingProps) {
    // How long the answer has taken so far
    const [start] = useState(Date.now);
    const now = useNow();
    const seconds = Math.floor((now - start) / 1000);
    const took = seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;

    return (
        <div className="flex items-center gap-2 text-xs">
            <span className="size-1.5 shrink-0 animate-blink rounded-full bg-accent" />
            <span className="text-dim tabular-nums">{took}</span>
            <span className="text-ghost" aria-hidden="true">
                ·
            </span>
            <span role="status">
                <span key={stage ?? 'working'} className={`shimmer ${TICK}`}>
                    {stage === null ? 'Working' : LABELS[stage]}
                </span>
            </span>
        </div>
    );
}

export default Thinking;
