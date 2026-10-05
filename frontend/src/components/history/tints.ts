import { Ban, Bell, CircleParking, Clock, Info, TrainFront } from 'lucide-react';
import type { Intent } from '@/types/answer';
import type { Kind, Tally } from '@/lib/insights';

// What a refusal draws
const REFUSAL = {
    Icon: Ban,
    tile: 'bg-bubble text-ghost',
    pill: 'border-seam bg-bubble text-hush',
    label: 'Refused',
};

// What a domain draws
const KINDS: Record<Intent, { Icon: typeof Clock; tile: string; pill?: string; label: string }> = {
    route: {
        Icon: TrainFront,
        tile: 'bg-red-fill/12 text-red',
        pill: 'border-red-fill/26 bg-red-fill/10 text-red',
        label: 'Route',
    },
    schedule: {
        Icon: Clock,
        tile: 'bg-blue-fill/12 text-blue',
        pill: 'border-blue-fill/26 bg-blue-fill/10 text-blue',
        label: 'Schedule',
    },
    alert: { Icon: Bell, tile: 'bg-amber/12 text-amber', label: 'Alerts' },
    'parking-rules': {
        Icon: CircleParking,
        tile: 'bg-commuter-fill/12 text-commuter',
        label: 'Parking rules',
    },
    info: { Icon: Info, tile: 'bg-bubble text-muted', label: 'Info' },
    'off-topic': REFUSAL,
};

export function lookOf(kind: Kind) {
    return kind === 'refused' ? REFUSAL : KINDS[kind];
}

// The color each intent takes in the charts
export const FILLS: Record<Kind, string> = {
    route: 'bg-red-fill',
    schedule: 'bg-blue-fill',
    alert: 'bg-amber',
    info: 'bg-quiet',
    refused: 'bg-ghost',
    'off-topic': 'bg-ghost',
    'parking-rules': 'bg-commuter-fill',
};

// A panel beside the list
export const CARD = 'rounded-tile border border-seam bg-panel p-4 shadow-card';

// A count with its noun
export function questionsOf(count: number) {
    return `${count} ${count === 1 ? 'question' : 'questions'}`;
}

// What a screen reader says for a bar
export function ariaLabelOf(bar: Tally) {
    const parts = bar.parts.map(([kind, count]) => `${count} ${lookOf(kind).label}`).join(', ');
    return `${bar.name}: ${questionsOf(bar.total)}, ${parts}`;
}
