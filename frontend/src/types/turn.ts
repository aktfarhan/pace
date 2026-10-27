import type { Answer, Picked } from '@/types/answer';

// One question and its answer
export interface Turn {
    id: number;
    query: string;
    pick?: Picked;
    answer: Answer | null;
    failed: boolean;
    said?: string;
}

// The parts of a turn that can be written after it opens
export type TurnFields = Partial<Omit<Turn, 'id'>>;
