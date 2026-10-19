import type { Drawn } from '@/lib/lines';
import type { Emphasis } from './useEmphasis';

interface PathsProps {
    drawn: { line: Drawn; path: string }[];
    lead: string | null;
    strengthOf: Emphasis['strengthOf'];
}

function Paths({ drawn, lead, strengthOf }: PathsProps) {
    return (
        <>
            {drawn.map((one) => (
                <path
                    key={one.line.id}
                    d={one.path}
                    fill="none"
                    style={{
                        strokeWidth: lead === one.line.id ? 2.75 : 1.75,
                        strokeOpacity: strengthOf(one.line.id),
                    }}
                    strokeLinecap="round"
                    className={`${one.line.stroke} transition-[stroke-opacity,stroke-width] ease-out`}
                />
            ))}
        </>
    );
}

export default Paths;
