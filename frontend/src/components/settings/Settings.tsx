import Group from './Group';
import General from './General';
import Keeping from './Keeping';

function Settings() {
    return (
        <div className="@container flex flex-col gap-3.5">
            <h1 className="text-board text-bright">Settings</h1>
            <div className="grid @4xl:grid-cols-2">
                <div className="flex flex-col gap-3.5">
                    <Group label="General">
                        <General />
                    </Group>
                    <Group label="History">
                        <Keeping />
                    </Group>
                </div>
            </div>
        </div>
    );
}

export default Settings;
