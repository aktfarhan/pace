import PlaceForm from './PlaceForm';
import { flushSync } from 'react-dom';
import { useRef, useState } from 'react';
import { MapPin, Plus } from 'lucide-react';
import Empty from '@/components/layout/Empty';

interface AddPlaceProps {
    keep: (label: string, address: string) => Promise<void>;
    first: boolean;
}

function AddPlace({ keep, first }: AddPlaceProps) {
    const [open, setOpen] = useState(false);
    const tileRef = useRef<HTMLButtonElement>(null);

    // Closes the form and focuses the tile
    const close = () => {
        flushSync(() => setOpen(false));
        tileRef.current?.focus();
    };

    // The form takes its own row
    if (open) return <PlaceForm keep={keep} close={close} />;

    // Empty state for no places
    if (first) {
        return (
            <div className="col-span-full">
                <Empty
                    Icon={MapPin}
                    title="Places you save show up here"
                    note="Save home, work and more."
                    action="Add a place"
                    ActionIcon={Plus}
                    run={() => setOpen(true)}
                    ref={tileRef}
                />
            </div>
        );
    }

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
