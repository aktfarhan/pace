import { useAsk } from '@/hooks/useAsk';
import TurnList from '@/components/ask/TurnList';
import AskInput from '@/components/ask/AskInput';

function App() {
    const { turns, stage, busy, send } = useAsk();

    return (
        <main className="mx-auto flex min-h-dvh max-w-2xl flex-col justify-between gap-6 p-8">
            <TurnList turns={turns} stage={stage} />
            <AskInput send={send} busy={busy} />
        </main>
    );
}

export default App;
