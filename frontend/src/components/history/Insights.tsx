import Week from './Week';
import Kinds from './Kinds';
import Hours from './Hours';
import type { Kind } from '@/lib/insights';
import type { Entry } from '@/types/history';

interface InsightsProps {
    entries: Entry[];
    picked: Kind | null;
    pick: (kind: Kind | null) => void;
    jump: (key: string) => void;
}

function Insights({ entries, picked, pick, jump }: InsightsProps) {
    return (
        <aside className="flex flex-col gap-3 @4xl:sticky @4xl:top-0 @4xl:mt-9 @4xl:w-76 @4xl:shrink-0">
            <Week entries={entries} jump={jump} />
            <Kinds entries={entries} picked={picked} pick={pick} />
            <Hours entries={entries} />
        </aside>
    );
}

export default Insights;
