"use client";

type ZoneCardProps = {
  title: string;
  clusterId: number;
  fields: string[];
};

export function ZoneCard({ title, clusterId, fields }: ZoneCardProps) {
  return (
    <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-farm-accent">{title}</h3>
        <span className="rounded-full bg-green-900/30 px-2 py-1 text-[10px]">Cluster {clusterId}</span>
      </div>
      <div className="space-y-1 text-sm text-gray-300">
        {fields.length === 0 ? <p>No fields mapped.</p> : fields.map((field) => <p key={field}>{field}</p>)}
      </div>
    </div>
  );
}
