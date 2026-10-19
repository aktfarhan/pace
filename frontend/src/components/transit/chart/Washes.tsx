import Wash from './Wash';
import type { Box } from './plot';
import type { Drawn } from '@/lib/lines';
import type { Emphasis } from './useEmphasis';

interface WashesProps {
    drawn: { line: Drawn; under: string }[];
    box: Box;
    strengthOf: Emphasis['strengthOf'];
}

function Washes({ drawn, box, strengthOf }: WashesProps) {
    return (
        <>
            {drawn.map((one) => (
                <g
                    key={one.line.id}
                    style={{ opacity: strengthOf(one.line.id) }}
                    className="transition-opacity ease-out"
                >
                    <Wash path={one.under} text={one.line.text} box={box} upTo={null} soft />
                </g>
            ))}
        </>
    );
}

export default Washes;
