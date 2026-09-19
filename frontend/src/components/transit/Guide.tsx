import type { Box, Spot } from './plot';

interface GuideProps {
    spot: Spot;
    box: Box;
}

// The line down the chart at the spot being hovered
function Guide({ spot, box }: GuideProps) {
    return (
        <line
            x1={spot.x}
            y1={box.ceil}
            x2={spot.x}
            y2={box.floor}
            className="stroke-edge"
            strokeWidth={1}
        />
    );
}

export default Guide;
