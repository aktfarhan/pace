import { CARD } from './tints';
import KindRow from './KindRow';
import { kindsOf } from '@/lib/insights';
import type { Kind } from '@/lib/insights';
import type { Entry } from '@/types/history';

interface KindsProps {
    entries: Entry[];
    picked: Kind | null;
    pick: (kind: Kind | null) => void;
}

function Kinds({ entries, picked, pick }: KindsProps) {
    return (
        <section className={CARD}>
            <h2 className="text-title text-bright">What you asked</h2>
            <ul className="-mx-2 mt-2 flex flex-col gap-0.5">
                {kindsOf(entries).map(([kind, count]) => (
                    <li key={kind}>
                        <KindRow
                            kind={kind}
                            count={count}
                            share={count / entries.length}
                            picked={picked === kind}
                            pick={() => pick(picked === kind ? null : kind)}
                        />
                    </li>
                ))}
            </ul>
        </section>
    );
}

export default Kinds;
