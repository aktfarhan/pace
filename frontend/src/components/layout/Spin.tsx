import clsx from 'clsx';
import { useState } from 'react';
import { RotateCw } from 'lucide-react';

interface SpinProps {
    on: boolean;
}

function Spin({ on }: SpinProps) {
    const [spinning, setSpinning] = useState(on);
    if (on && !spinning) setSpinning(true);

    return (
        <RotateCw
            size={12}
            strokeWidth={2.4}
            className={clsx('text-quiet', spinning && 'animate-spin')}
            onAnimationIteration={() => {
                if (!on) setSpinning(false);
            }}
        />
    );
}

export default Spin;
