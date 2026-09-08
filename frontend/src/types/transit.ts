import type { SystemStatus } from '@/types/status';

// One line's share of late arrivals in 15min
export interface Reading {
    at: string;
    share: number;
    seen: number;
}

// What /v1/transit returns
export interface Transit {
    status: SystemStatus;
    series: Record<string, Reading[]>;
}
