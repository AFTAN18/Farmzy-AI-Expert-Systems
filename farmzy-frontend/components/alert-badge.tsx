"use client";

import type { AlertItem } from "@/lib/types";

type AlertBadgeProps = {
  alert: AlertItem;
};

export function AlertBadge({ alert }: AlertBadgeProps) {
  const color =
    alert.severity === "critical"
      ? "border-red-500/50 bg-red-950/30 text-red-300"
      : alert.severity === "warning"
        ? "border-amber-500/50 bg-amber-950/30 text-amber-300"
        : "border-sky-500/50 bg-sky-950/30 text-sky-300";

  return (
    <div className={`rounded-lg border p-3 ${color}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.2em]">{alert.alert_type}</span>
        <span className="text-xs">{alert.severity}</span>
      </div>
      <p className="mt-2 text-sm">{alert.message}</p>
    </div>
  );
}
