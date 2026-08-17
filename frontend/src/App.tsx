import { useAsk } from '@/hooks/useAsk';
import TurnList from '@/components/ask/TurnList';
import AskInput from '@/components/ask/AskInput';
import Sidebar from '@/components/layout/sidebar/Sidebar';

function App() {
    const { turns, stage, busy, send, refresh, refreshing } = useAsk();

    return (
        <div className="flex h-dvh">
            <Sidebar />
            <main className="flex flex-1 flex-col gap-6 p-8">
                <TurnList turns={turns} stage={stage} refresh={refresh} refreshing={refreshing} />
                <AskInput send={send} busy={busy} />
            </main>
        </div>
    );
}

export default App;
