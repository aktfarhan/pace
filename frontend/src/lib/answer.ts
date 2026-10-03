// Splits an answer into its lines
export function linesOf(text: string) {
    const lines = [];
    for (const raw of text.split('\n')) {
        const line = raw.trim();
        if (line === '') continue;

        const bullet = line.startsWith('- ');
        lines.push({ bullet, text: bullet ? line.slice(2) : line });
    }
    return lines;
}
