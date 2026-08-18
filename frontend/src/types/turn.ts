import type { Answer } from '@/types/answer';

// One question and its answer
export interface Turn {
    id: number;
    query: string;
    answer: Answer | null;
    failed: boolean;
}

// The parts of a turn that can be written after it opens
export type TurnFields = Partial<Omit<Turn, 'id'>>;
