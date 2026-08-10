// What /v1/ask returns
export interface Answer {
    answer: string;
    sources: string[];
    risk: string | null;
    should_refuse: boolean;
    refuse_reason: string | null;
}

// A stage the pipeline reports
export type Stage = 'classify' | 'retrieve' | 'plan' | 'alerts' | 'departures' | 'generate';
