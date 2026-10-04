import { Plus } from 'lucide-react';
import PlaceForm from './PlaceForm';
import { flushSync } from 'react-dom';
import { useRef, useState } from 'react';

interface AddPlaceProps {
    keep: (label: string, address: string) => Promise<void>;
}

function AddPlace({ keep }: AddPlaceProps) {
    const [open, setOpen] = useState(false);
    const tileRef = useRef<HTMLButtonElement>(null);

    // Closes the form and focuses the tile
    const close = () => {
        flushSync(() => setOpen(false));
        tileRef.current?.focus();
    };

    // The form takes its own row
    if (open) return <PlaceForm keep={keep} close={close} />;

    return (
        <button
            ref={tileRef}
            type="button"
            onClick={() => setOpen(true)}
            className="flex min-h-31 cursor-pointer flex-col items-center justify-center gap-2.25 rounded-tile border border-dashed border-line px-4.25 py-4 text-dim transition ease-out hover:border-edge hover:bg-panel hover:text-soft active:scale-98"
        >
            <Plus size={19} strokeWidth={1.9} />
            <span className="font-mono text-pill uppercase">Add a place</span>
        </button>
    );
}

export default AddPlace;
