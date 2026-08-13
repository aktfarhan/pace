// How a line is running
export type State = 'clear' | 'notice' | 'disrupted' | 'severe';

// Fields every line has
interface LineFields {
    line_id: string;
    badge_text: string;
    line_name: string;
    branch_ids: string[];
    directions: number[];
    stop_count: number;
    alert_count: number;
}

// A line with no alert
interface ClearLine extends LineFields {
    state: 'clear';
    effect: null;
    cause: null;
    headline: null;
    alert_delay_minutes: null;
    since: null;
    until: null;
}

// A line with an alert
export interface AlertedLine extends LineFields {
    state: Exclude<State, 'clear'>;
    effect: string;
    cause: string | null;
    headline: string;
    alert_delay_minutes: [number, number] | null;
    since: string | null;
    until: string | null;
}

export type LineStatus = ClearLine | AlertedLine;

// What /v1/status returns
export interface SystemStatus {
    lines: LineStatus[];
    clear_count: number;
    retrieved_at: string;
    ok: boolean;
}
