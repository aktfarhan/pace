import Group from './Group';
import General from './General';

function Settings() {
    return (
        <div className="@container flex flex-col gap-3.5">
            <h1 className="text-board text-bright">Settings</h1>
            <div className="grid @4xl:grid-cols-2">
                <Group label="General">
                    <General />
                </Group>
            </div>
        </div>
    );
}

export default Settings;
