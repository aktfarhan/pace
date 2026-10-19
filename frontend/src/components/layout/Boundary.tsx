import Failed from './Failed';
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

const BROKEN = 'Something went wrong';

interface BoundaryProps {
    children: ReactNode;
}

interface BoundaryState {
    broken: boolean;
}

// One broken page shows a note
class Boundary extends Component<BoundaryProps, BoundaryState> {
    state: BoundaryState = { broken: false };

    static getDerivedStateFromError(): BoundaryState {
        return { broken: true };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error(error, info.componentStack);
    }

    render() {
        if (this.state.broken) {
            return <Failed said={BROKEN} retry={() => window.location.reload()} />;
        }
        return this.props.children;
    }
}

export default Boundary;
