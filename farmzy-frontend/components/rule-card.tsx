"use client";

import type { RuleItem } from "@/lib/types";

type RuleCardProps = {
  rule: RuleItem;
  onToggle: (rule: RuleItem) => void;
};

export function RuleCard({ rule, onToggle }: RuleCardProps) {
  return (
    <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="rounded-full bg-green-900/30 px-2 py-1 text-xs text-farm-accent">{rule.rule_id}</span>
        <button
          className="rounded-md border border-green-700/40 px-2 py-1 text-xs text-gray-200"
          onClick={() => onToggle({ ...rule, is_active: !rule.is_active })}
        >
          {rule.is_active ? "Disable" : "Enable"}
        </button>
      </div>
      <h3 className="text-sm font-semibold">{rule.rule_name}</h3>
      <p className="mt-2 rounded-md bg-green-950/30 p-2 font-mono text-xs text-green-300">IF {rule.condition_description}</p>
      <p className="mt-2 rounded-md bg-amber-950/30 p-2 font-mono text-xs text-amber-300">THEN {rule.action_description}</p>
      <p className="mt-2 text-xs text-gray-400">Priority: {rule.priority}</p>
    </div>
  );
}
