import Segmented from '@/components/layout/Segmented';

// The stretches of the day for the main chart
const SPANS = [
    { label: 'Day', hours: null },
    { label: '6h', hours: 6 },
    { label: '3h', hours: 3 },
] as const;

const LABELS = SPANS.map((one) => one.label);

interface RangeProps {
    span: number | null;
    select: (hours: number | null) => void;
}

function Range({ span, select }: RangeProps) {
    const value = SPANS.find((one) => one.hours === span)?.label ?? 'Day';

    return (
        <Segmented
            label="How much of the day to show"
            options={LABELS}
            value={value}
            pick={(label) => select(SPANS.find((one) => one.label === label)?.hours ?? null)}
        />
    );
}

export default Range;
