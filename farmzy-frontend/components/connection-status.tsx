"use client";

type ConnectionStatusProps = {
  channel: string;
  connected: boolean;
  lastSyncSeconds: number;
};

export function ConnectionStatus({ channel, connected, lastSyncSeconds }: ConnectionStatusProps) {
  return (
    <div className="rounded-lg border border-green-700/40 bg-farm-surface/90 px-4 py-2 text-sm">
      <span className={connected ? "text-farm-accent" : "text-red-400"}>{connected ? "Connected" : "Disconnected"}</span>
      {` to ThingSpeak Channel ${channel} · Last sync: ${lastSyncSeconds}s ago`}
    </div>
  );
}
