const FAILED = "Couldn't save this place. Check the address and try again.";

interface PlaceActionsProps {
    failed: boolean;
    saving: boolean;
    ready: boolean;
    close: () => void;
}

function PlaceActions({ failed, saving, ready, close }: PlaceActionsProps) {
    return (
        <div className="flex flex-wrap items-center gap-2">
            {failed && (
                <span role="alert" className="w-full min-w-0 text-row text-red sm:w-auto sm:flex-1">
                    {FAILED}
                </span>
            )}
            <button
                type="button"
                onClick={close}
                disabled={saving}
                className="ml-auto h-10 cursor-pointer rounded-xl px-4 text-sm text-dim transition ease-out hover:bg-field hover:text-cream active:scale-97 disabled:cursor-default disabled:opacity-40"
            >
                Cancel
            </button>
            <button
                type="submit"
                disabled={!ready || saving}
                className="h-10 cursor-pointer rounded-xl bg-accent px-4.5 text-sm font-semibold text-onaccent transition ease-out enabled:hover:bg-bright enabled:active:scale-97 disabled:cursor-default disabled:opacity-30"
            >
                Save place
            </button>
        </div>
    );
}

export default PlaceActions;
