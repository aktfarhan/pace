import type { Line } from '@/lib/lines';
import type { LineAlert, SystemStatus } from '@/types/status';

// One line's share of late arrivals across the stretch before it
export interface Reading {
    at: string;
    share: number;
    seen: number;
    reach: number;
}

// Today versus earlier days
export interface TypicalReading extends Reading {
    days: number;
}

// What /v1/readings returns, once a quarter hour
export interface Readings {
    series: Record<string, Reading[]>;
    typical: Record<string, TypicalReading[]>;
}

// What /v1/transit returns
export interface Live {
    status: SystemStatus;
    readings: string;
    headways: Partial<Record<string, number>>;
    resumes: Partial<Record<string, string>>;
    timetable: boolean;
    branches: Partial<Record<string, Branch[]>>;
    late_minutes: number;
    rolling_minutes: number;
}

// The live state and the readings together
export type Transit = Live & Readings;

// One route a line runs under its main
interface Branch {
    id: string;
    name: string;
}

// The branch picker's line and its branches
export interface Branching {
    line: Line;
    branches: Branch[];
    branch: string | null;
    pick: (branch: string | null) => void;
    shares: Record<string, number | null>;
}

// One line or branch, and how it is running
export interface Standing {
    id: string;
    code: string;
    name: string;
    chip: string;
    text: string;
    share: number | null;
    drift: number | null;
    every: number | null;
    next: string | null;
    started: boolean;
    timetable: boolean;
    trend: { at: number; share: number }[];
}

// One alert with every line it names
export interface Notice {
    lines: Line[];
    alert: LineAlert;
}
