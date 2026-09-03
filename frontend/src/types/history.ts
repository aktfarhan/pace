import type { Intent } from '@/types/answer';

// One answered question
export interface Entry {
    at: string;
    query: string;
    intent: Intent;
    refused: boolean;
    detail: string;
    chip: string | null;
}
