import { RotateCw } from 'lucide-react';

interface TryAgainProps {
    retry: () => void;
}

function TryAgain({ retry }: TryAgainProps) {
    return (
        <button
            type="button"
            onClick={retry}
            className="relative flex cursor-pointer items-center gap-1 text-cream transition-transform ease-out active:scale-97 pointer-coarse:after:absolute pointer-coarse:after:-inset-x-2 pointer-coarse:after:-inset-y-3"
        >
            <RotateCw size={13} strokeWidth={2.2} />
            Try again
        </button>
    );
}

export default TryAgain;
