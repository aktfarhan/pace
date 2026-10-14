import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import type { TransitionEvent } from 'react';

// The hold button
const PILL =
    'group relative flex cursor-pointer items-center gap-1.75 overflow-hidden rounded-full border border-seam bg-field py-1.5 pr-3.5 pl-3 font-mono text-tag text-soft uppercase transition ease-out select-none hover:border-red-fill/30 hover:text-red data-held:scale-97';

// The fill that crosses while held
const FILL =
    'absolute inset-0 origin-left scale-x-0 bg-red-fill/22 transition-transform duration-200 ease-out group-data-held:scale-x-100 group-data-held:duration-1500 group-data-held:ease-linear';

interface HoldProps {
    label: string;
    done: () => void;
}

function Hold({ label, done }: HoldProps) {
    const [held, setHeld] = useState(false);

    // Clears once when its fully filled
    const crossed = (event: TransitionEvent<HTMLSpanElement>) => {
        if (event.propertyName === 'scale' && held) done();
    };

    return (
        <button
            type="button"
            className={PILL}
            data-held={held || undefined}
            onPointerDown={() => setHeld(true)}
            onPointerUp={() => setHeld(false)}
            onPointerLeave={() => setHeld(false)}
            onPointerCancel={() => setHeld(false)}
        >
            <span className={FILL} onTransitionEnd={crossed} />
            <Trash2 size={12} strokeWidth={2.2} className="relative" />
            <span className="relative">{label}</span>
        </button>
    );
}

export default Hold;
