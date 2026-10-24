import { useId } from 'react';
import type { Box } from './plot';

interface WashProps {
    path: string;
    text: string;
    box: Box;
    upTo: number | null;
}

function Wash({ path, text, box, upTo }: WashProps) {
    const tint = useId();
    const mask = useId();

    return (
        <>
            <defs>
                <linearGradient
                    id={tint}
                    gradientUnits="userSpaceOnUse"
                    x2="0"
                    y1={box.ceil}
                    y2={box.floor}
                    className={text}
                >
                    <stop stopColor="currentColor" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="currentColor" stopOpacity={0.05} />
                </linearGradient>
                {upTo !== null && (
                    <mask id={mask}>
                        <rect width="100%" height="100%" fill="white" fillOpacity={0.35} />
                        <rect width={upTo} height="100%" fill="white" />
                    </mask>
                )}
            </defs>
            <path
                d={path}
                fill={`url(#${tint})`}
                mask={upTo === null ? undefined : `url(#${mask})`}
            />
        </>
    );
}

export default Wash;
