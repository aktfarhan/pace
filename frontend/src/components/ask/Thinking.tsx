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
    stage: Stage;
}

function Thinking({ stage }: ThinkingProps) {
    return (
        <div className="flex items-center gap-2">
            <span className="size-1.5 shrink-0 animate-blink rounded-full bg-brass" />
            <span className="text-xs text-dim">{LABELS[stage]}</span>
        </div>
    );
}

export default Thinking;
