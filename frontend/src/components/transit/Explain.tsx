import { Info } from 'lucide-react';
import { WAIT_MS } from '@/hooks/useTip';
import { useEffect, useEffectEvent, useId, useRef, useState } from 'react';

interface ExplainProps {
    late: number;
    rolling: number;
}

function Explain({ late, rolling }: ExplainProps) {
    const id = useId();
    const [open, setOpen] = useState(false);
    const timer = useRef(0);

    // Drops a pending open when the chart goes away
    useEffect(() => {
        const pending = timer;
        return () => window.clearTimeout(pending.current);
    }, []);

    // Opens instant on a click or after a delay on hover
    const show = (now: boolean) => {
        window.clearTimeout(timer.current);
        if (now) setOpen(true);
        else timer.current = window.setTimeout(() => setOpen(true), WAIT_MS);
    };

    // Closes and cancels a pending open
    const hide = () => {
        window.clearTimeout(timer.current);
        setOpen(false);
    };

    // A tap elsewhere puts it away
    const dismiss = useEffectEvent(hide);

    // Taps on the button or its tooltip don't exit
    const boxRef = useRef<HTMLSpanElement>(null);
    useEffect(() => {
        if (!open) return;
        const away = ({ target }: PointerEvent) => {
            if (!(target instanceof Node && boxRef.current?.contains(target))) dismiss();
        };
        document.addEventListener('pointerdown', away);
        return () => document.removeEventListener('pointerdown', away);
    }, [open]);

    const span = rolling === 60 ? 'hour' : `${rolling} minutes`;

    return (
        <span ref={boxRef}>
            <button
                type="button"
                aria-label="What counts as late"
                aria-describedby={open ? id : undefined}
                aria-expanded={open}
                onClick={() => (open ? hide() : show(true))}
                onPointerEnter={(event) => event.pointerType !== 'touch' && show(false)}
                onPointerLeave={(event) => event.pointerType !== 'touch' && hide()}
                onBlur={hide}
                onKeyDown={(event) => event.key === 'Escape' && hide()}
                className="-m-1.5 grid size-8 cursor-pointer place-items-center rounded-full text-faint transition ease-out hover:text-soft active:scale-96"
            >
                <Info size={13} strokeWidth={2} />
            </button>
            {open && (
                <span
                    id={id}
                    role="tooltip"
                    className="absolute top-full left-0 z-20 mt-2 w-72 max-w-full origin-top-left rounded-chip border border-edge bg-bubble px-3 py-2.5 text-xs/relaxed text-soft shadow-float transition duration-125 ease-out starting:scale-97 starting:opacity-0 motion-reduce:starting:scale-100"
                >
                    Each point is the share of arrivals more than {late} minutes behind schedule,
                    over the previous {span}.
                </span>
            )}
        </span>
    );
}

export default Explain;
