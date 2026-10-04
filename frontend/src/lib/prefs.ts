// The chart's spans on History
export const SPANS = ['Day', 'Week'] as const;
export type Span = (typeof SPANS)[number];
