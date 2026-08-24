import { Plus } from 'lucide-react';
import { useState, type SubmitEvent } from 'react';

const TILE = 'min-h-31 rounded-tile border border-dashed border-line px-4.25 py-4';

const FIELD =
    'w-full rounded-chip border border-line bg-field px-2.5 py-1.5 text-row text-cream outline-none placeholder:text-ghost focus:border-edge';

const BUTTON = 'cursor-pointer rounded-full border px-3 py-1.25 font-mono text-tag uppercase';

// The lengths the server accepts
const MAX_LABEL = 60;
const MAX_ADDRESS = 200;

interface AddPlaceProps {
    keep: (label: string, address: string) => Promise<void>;
}

function AddPlace({ keep }: AddPlaceProps) {
    const [open, setOpen] = useState(false);
    const [label, setLabel] = useState('');
    const [address, setAddress] = useState('');
    const [saving, setSaving] = useState(false);

    const ready = label.trim() !== '' && address.trim() !== '';

    const close = () => {
        setOpen(false);
        setLabel('');
        setAddress('');
    };

    const save = async (event: SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!ready || saving) return;

        setSaving(true);
        try {
            await keep(label.trim(), address.trim());
            close();
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    };

    if (!open)
        return (
            <button
                type="button"
                onClick={() => setOpen(true)}
                className={`${TILE} flex cursor-pointer flex-col items-center justify-center gap-2.25 text-ghost transition-colors hover:border-edge hover:text-hush`}
            >
                <Plus size={19} strokeWidth={1.9} aria-hidden="true" />
                <span className="font-mono text-pill uppercase">Add a place</span>
            </button>
        );

    return (
        <form onSubmit={save} className={`${TILE} flex flex-col gap-2`}>
            <input
                autoFocus
                value={label}
                maxLength={MAX_LABEL}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="Home"
                aria-label="Place name"
                className={FIELD}
            />
            <input
                value={address}
                maxLength={MAX_ADDRESS}
                onChange={(event) => setAddress(event.target.value)}
                placeholder="1 Main Street"
                aria-label="Place address"
                className={FIELD}
            />
            <div className="mt-0.5 flex items-center gap-2">
                <button
                    type="submit"
                    disabled={!ready || saving}
                    className={`${BUTTON} border-edge bg-bubble text-cream hover:border-ghost disabled:cursor-default disabled:text-ghost`}
                >
                    Save
                </button>
                <button
                    type="button"
                    onClick={close}
                    disabled={saving}
                    className={`${BUTTON} border-transparent text-dim hover:text-cream disabled:text-ghost`}
                >
                    Cancel
                </button>
            </div>
        </form>
    );
}

export default AddPlace;
