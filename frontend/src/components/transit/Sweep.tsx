import { useId, type ReactNode } from 'react';

interface SweepProps {
    shown: string;
    left: number;
    width: number;
    height: number;
    children: ReactNode;
}

function Sweep({ shown, left, width, height, children }: SweepProps) {
    const clip = useId();

    return (
        <>
            <defs>
                <clipPath id={clip}>
                    <rect
                        key={shown}
                        x={left}
                        width={Math.max(width - left, 0)}
                        height={height}
                        className="animate-sweep motion-reduce:animate-none"
                        style={{ transformBox: 'fill-box', transformOrigin: 'left' }}
                    />
                </clipPath>
            </defs>
            <g clipPath={`url(#${clip})`}>{children}</g>
        </>
    );
}

export default Sweep;
