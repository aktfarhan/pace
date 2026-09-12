// Every line the app draws
export const LINES = [
    {
        id: 'Red',
        label: 'Red',
        code: 'RL',
        text: 'text-red',
        fill: 'bg-red-fill',
        chip: 'border-red-fill/28 bg-red-fill/12 text-red',
        tile: 'border-red/28 bg-red/12 text-red',
        tag: 'border-red-fill/26 bg-red-fill/12 text-red',
        tagHit: 'border-red-fill/40 bg-red-fill/12 text-red',
    },
    {
        id: 'Mattapan',
        label: 'Mattapan',
        code: 'M',
        text: 'text-mattapan',
        fill: 'bg-mattapan-fill',
        chip: 'border-mattapan-fill/28 bg-mattapan-fill/12 text-mattapan',
        tile: 'border-mattapan/28 bg-mattapan/12 text-mattapan',
        tag: 'border-mattapan-fill/26 bg-mattapan-fill/12 text-mattapan',
        tagHit: 'border-mattapan-fill/40 bg-mattapan-fill/12 text-mattapan',
    },
    {
        id: 'Orange',
        label: 'Orange',
        code: 'OL',
        text: 'text-orange',
        fill: 'bg-orange-fill',
        chip: 'border-orange-fill/28 bg-orange-fill/12 text-orange',
        tile: 'border-orange/28 bg-orange/12 text-orange',
        tag: 'border-orange-fill/26 bg-orange-fill/12 text-orange',
        tagHit: 'border-orange-fill/40 bg-orange-fill/12 text-orange',
    },
    {
        id: 'Green',
        label: 'Green',
        code: 'GL',
        text: 'text-green',
        fill: 'bg-green-fill',
        chip: 'border-green-fill/28 bg-green-fill/12 text-green',
        tile: 'border-green/30 bg-green/12 text-green',
        tag: 'border-green-fill/26 bg-green-fill/12 text-green',
        tagHit: 'border-green-fill/40 bg-green-fill/12 text-green',
    },
    {
        id: 'Blue',
        label: 'Blue',
        code: 'BL',
        text: 'text-blue',
        fill: 'bg-blue-fill',
        chip: 'border-blue-fill/28 bg-blue-fill/12 text-blue',
        tile: 'border-blue/28 bg-blue/12 text-blue',
        tag: 'border-blue-fill/26 bg-blue-fill/12 text-blue',
        tagHit: 'border-blue-fill/40 bg-blue-fill/12 text-blue',
    },
    {
        id: 'CR',
        label: 'Commuter',
        code: 'CR',
        text: 'text-commuter',
        fill: 'bg-commuter-fill',
        chip: 'border-commuter-fill/28 bg-commuter-fill/12 text-commuter',
        tile: 'border-commuter/28 bg-commuter/12 text-commuter',
        tag: 'border-commuter-fill/26 bg-commuter-fill/12 text-commuter',
        tagHit: 'border-commuter-fill/40 bg-commuter-fill/12 text-commuter',
    },
] as const;

const BUS = {
    id: 'Bus',
    text: 'text-bus',
    fill: 'bg-bus-fill',
    chip: 'border-bus-fill/28 bg-bus-fill/12 text-bus',
    tile: 'border-bus/28 bg-bus/12 text-bus',
};

// The label a line carries
export type LineLabel = (typeof LINES)[number]['label'];

// Each line's row
export const LINE_BY_ID: Record<string, (typeof LINES)[number]> = {};
for (const line of LINES) {
    LINE_BY_ID[line.id] = line;
}

// route_id -> the tint it wears, or null
export function tintOf(routeId: string) {
    if (/^\d+$/.test(routeId)) return BUS;
    if (routeId.startsWith('Green-')) return LINE_BY_ID.Green;
    if (routeId.startsWith('CR-')) return LINE_BY_ID.CR;
    return LINE_BY_ID[routeId] ?? null;
}
