import type { Line } from '@/lib/lines';
import type { SystemStatus } from '@/types/status';

// One line's share of late arrivals across the stretch before it
export interface Reading {
    at: string;
    share: number;
    seen: number;
    reach: number;
    days?: number;
}

// What /v1/transit returns
export interface Transit {
    status: SystemStatus;
    series: Record<string, Reading[]>;
    typical: Record<string, Reading[]>;
    headways: Record<string, number>;
    resumes: Record<string, string>;
    branches: Record<string, Branch[]>;
    late_minutes: number;
    rolling_minutes: number;
}

// One route a line runs under its main
export interface Branch {
    id: string;
    name: string;
}

// The branch picker's line and its branches
export interface Branching {
    line: Line;
    branches: Branch[];
    branch: string | null;
    pick: (branch: string | null) => void;
}
