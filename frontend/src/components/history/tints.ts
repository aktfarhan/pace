import { Ban, Bell, CircleParking, Clock, Info, TrainFront } from 'lucide-react';
import type { Intent } from '@/types/answer';

// What a refusal draws
export const REFUSAL = {
    Icon: Ban,
    tile: 'bg-bubble text-ghost',
    pill: 'border-seam bg-bubble text-hush',
    label: 'Refused',
};

// What a domain draws
export const KINDS: Record<
    Intent,
    { Icon: typeof Clock; tile: string; pill?: string; label: string }
> = {
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
