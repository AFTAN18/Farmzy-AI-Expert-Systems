"use client";

import { FormEvent, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { RuleCard } from "@/components/rule-card";
import { api } from "@/lib/api";
import type { RuleItem } from "@/lib/types";

export default function RulesPage() {
  const query = useQuery({ queryKey: ["rules"], queryFn: () => api.getRules() });

  const [newRule, setNewRule] = useState<RuleItem>({
    rule_id: "RULE_",
    rule_name: "",
    condition_description: "",
    action_description: "",
    priority: 50,
    is_active: true,
  });

  async function handleToggle(rule: RuleItem) {
    await api.updateRule(rule.rule_id, rule);
    query.refetch();
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await api.createRule(newRule);
    setNewRule({
      rule_id: "RULE_",
      rule_name: "",
      condition_description: "",
      action_description: "",
      priority: 50,
      is_active: true,
    });
    query.refetch();
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-farm-muted">Add Custom Rule</p>
        <div className="grid gap-2 md:grid-cols-2">
          <input
            className="rounded-md border border-green-700/40 bg-green-950/30 px-2 py-1"
            placeholder="Rule ID"
            value={newRule.rule_id}
            onChange={(e) => setNewRule((prev) => ({ ...prev, rule_id: e.target.value }))}
          />
          <input
            className="rounded-md border border-green-700/40 bg-green-950/30 px-2 py-1"
            placeholder="Rule Name"
            value={newRule.rule_name}
            onChange={(e) => setNewRule((prev) => ({ ...prev, rule_name: e.target.value }))}
          />
          <input
            className="rounded-md border border-green-700/40 bg-green-950/30 px-2 py-1 md:col-span-2"
            placeholder="Condition"
            value={newRule.condition_description}
            onChange={(e) => setNewRule((prev) => ({ ...prev, condition_description: e.target.value }))}
          />
          <input
            className="rounded-md border border-green-700/40 bg-green-950/30 px-2 py-1 md:col-span-2"
            placeholder="Action"
            value={newRule.action_description}
            onChange={(e) => setNewRule((prev) => ({ ...prev, action_description: e.target.value }))}
          />
        </div>
        <button className="mt-3 rounded-md bg-farm-primary px-3 py-1 text-sm text-white" type="submit">
          Add Rule
        </button>
      </form>

      <section className="grid gap-3 md:grid-cols-2">
        {(query.data?.items ?? []).map((rule) => (
          <RuleCard key={rule.rule_id} rule={rule} onToggle={handleToggle} />
        ))}
      </section>
    </div>
  );
}
