import type { SystemStatus } from '@/types/status';

// One line's share of late arrivals across the stretch before it
export interface Reading {
    at: string;
    share: number;
    seen: number;
    reach: number;
}

// What /v1/transit returns
export interface Transit {
    status: SystemStatus;
    series: Record<string, Reading[]>;
}
