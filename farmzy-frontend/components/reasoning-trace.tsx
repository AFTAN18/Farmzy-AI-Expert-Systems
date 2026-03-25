"use client";

import { useState } from "react";

type ReasoningTraceProps = {
  trace: Record<string, unknown> | undefined;
};

function roundNumbers(value: unknown): unknown {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value : Number(value.toFixed(3));
  }
  if (Array.isArray(value)) {
    return value.map((item) => roundNumbers(item));
  }
  if (value && typeof value === "object") {
    const result: Record<string, unknown> = {};
    Object.entries(value as Record<string, unknown>).forEach(([key, val]) => {
      result[key] = roundNumbers(val);
    });
    return result;
  }
  return value;
}

export function ReasoningTrace({ trace }: ReasoningTraceProps) {
  const [open, setOpen] = useState(false);
  const cleanedTrace = roundNumbers(trace ?? {});

  return (
    <div className="rounded-lg border border-green-700/30 bg-green-950/20 p-3">
      <button className="text-xs uppercase tracking-[0.2em] text-farm-accent" onClick={() => setOpen((prev) => !prev)}>
        {open ? "Hide Reasoning Trace" : "Show Reasoning Trace"}
      </button>
      {open ? (
        <pre className="mt-3 overflow-x-auto rounded-md bg-black/30 p-3 text-xs text-gray-200">
          {JSON.stringify(cleanedTrace, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
