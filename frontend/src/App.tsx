import { useState } from 'react';
import { useAsk } from '@/hooks/useAsk';
import Saved from '@/components/saved/Saved';
import TurnList from '@/components/ask/TurnList';
import AskInput from '@/components/ask/AskInput';
import Transit from '@/components/transit/Transit';
import History from '@/components/history/History';
import Sidebar from '@/components/layout/sidebar/Sidebar';
import type { Page } from '@/components/layout/sidebar/tints';

function App() {
    const { turns, stage, busy, send, refresh, refreshing } = useAsk();
    const [sidebar, setSidebar] = useState(true);
    const [page, setPage] = useState<Page>('Ask');

    return (
        <div className="flex h-dvh">
            <Sidebar
                open={sidebar}
                toggle={() => setSidebar(!sidebar)}
                page={page}
                select={setPage}
            />
            <main className="flex min-h-0 min-w-0 flex-1 flex-col gap-6 overflow-y-auto p-8">
                {page === 'Ask' && (
                    <>
                        <TurnList
                            turns={turns}
                            stage={stage}
                            refresh={refresh}
                            refreshing={refreshing}
                        />
                        <AskInput send={send} busy={busy} />
                    </>
                )}
                {page === 'Saved' && <Saved />}
                {page === 'History' && <History />}
                {page === 'Transit' && <Transit />}
            </main>
        </div>
    );
}

export default App;
