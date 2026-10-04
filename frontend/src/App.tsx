import { flushSync } from 'react-dom';
import { pointing } from '@/lib/device';
import { useAsk } from '@/hooks/useAsk';
import { usePage } from '@/hooks/usePage';
import { setDraft } from '@/hooks/useDraft';
import Saved from '@/components/saved/Saved';
import { useStatus } from '@/hooks/useStatus';
import { ShowLine } from '@/hooks/useShowLine';
import { useLineTab } from '@/hooks/useLineTab';
import TurnList from '@/components/ask/TurnList';
import AskInput from '@/components/ask/AskInput';
import Transit from '@/components/transit/Transit';
import History from '@/components/history/History';
import { useShortcuts } from '@/hooks/useShortcuts';
import Drawer from '@/components/layout/sidebar/Drawer';
import Sidebar from '@/components/layout/sidebar/Sidebar';
import { Activity, useEffect, useRef, useState } from 'react';
import type { Page } from '@/components/layout/sidebar/tints';

function App() {
    const { turns, stage, busy, send, refresh, refreshing } = useAsk();
    const [sidebar, setSidebar] = useState(true);
    const { page, setPage, mainRef, remember } = usePage();
    const { tab, setTab, show } = useLineTab(setPage);
    const status = useStatus();

    // The question box
    const inputRef = useRef<HTMLInputElement>(null);

    // Go straight to the question box
    const toAsk = () => {
        flushSync(() => setPage('Ask'));
        inputRef.current?.focus();
    };

    // Choosing Ask while on it puts the cursor back
    const go = (next: Page) => {
        setPage(next);
        if (next === 'Ask' && pointing()) inputRef.current?.focus();
    };
    useShortcuts(go);

    // Arriving on Ask focuses on the box
    useEffect(() => {
        if (page === 'Ask' && pointing()) inputRef.current?.focus();
    }, [page]);

    // A picked starter leaves the cursor in the box
    const start = (query: string) => {
        send(query);
        if (pointing()) inputRef.current?.focus();
    };

    // Asks a History question again
    const askAgain = (query: string) => {
        setPage('Ask');
        if (busy) setDraft(query);
        else send(query);
    };

    return (
        <ShowLine value={show}>
            <div className="flex h-dvh flex-col sm:flex-row">
                <Drawer status={status} page={page} select={go} />
                <Sidebar
                    status={status}
                    open={sidebar}
                    toggle={() => setSidebar(!sidebar)}
                    page={page}
                    select={go}
                />
                <main
                    ref={mainRef}
                    onScroll={(event) => remember(event.currentTarget.scrollTop)}
                    className="flex min-h-0 min-w-0 flex-1 flex-col gap-6 overflow-y-auto p-5 sm:p-8"
                >
                    {page === 'Ask' && (
                        <>
                            <TurnList
                                turns={turns}
                                stage={stage}
                                refresh={refresh}
                                refreshing={refreshing}
                                ask={start}
                                status={status}
                            />
                            <AskInput
                                ref={inputRef}
                                send={send}
                                busy={busy}
                                asked={turns.map((turn) => turn.query)}
                            />
                        </>
                    )}
                    <Activity mode={page === 'Saved' ? 'visible' : 'hidden'}>
                        <Saved />
                    </Activity>
                    {page === 'History' && <History ask={askAgain} start={toAsk} />}
                    <Activity mode={page === 'Transit' ? 'visible' : 'hidden'}>
                        <Transit tab={tab} choose={setTab} />
                    </Activity>
                </main>
            </div>
        </ShowLine>
    );
}

export default App;
