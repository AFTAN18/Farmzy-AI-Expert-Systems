"use client";

type MetricCardProps = {
  label: string;
  value: string | number;
  subtitle?: string;
};

export function MetricCard({ label, value, subtitle }: MetricCardProps) {
  return (
    <div className="animate-[fadeIn_0.4s_ease] rounded-xl border border-green-700/30 bg-farm-surface/90 p-4 shadow-glow">
      <p className="text-xs uppercase tracking-[0.2em] text-farm-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-farm-accent">{value}</p>
      {subtitle ? <p className="mt-1 text-xs text-gray-400">{subtitle}</p> : null}
    </div>
  );
}
