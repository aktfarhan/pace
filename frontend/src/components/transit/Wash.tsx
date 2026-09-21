import { useId } from 'react';

interface WashProps {
    path: string;
    text: string;
}

function Wash({ path, text }: WashProps) {
    const tint = useId();

    return (
        <>
            <defs>
                <linearGradient id={tint} x2="0" y2="1" className={text}>
                    <stop offset="0%" stopColor="currentColor" stopOpacity={0.16} />
                    <stop offset="100%" stopColor="currentColor" stopOpacity={0} />
                </linearGradient>
            </defs>
            <path d={path} fill={`url(#${tint})`} />
        </>
    );
}

export default Wash;
