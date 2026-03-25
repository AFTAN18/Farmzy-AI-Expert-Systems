"use client";

import { useState } from "react";

type ReasoningTraceProps = {
  trace: Record<string, unknown> | undefined;
};

export function ReasoningTrace({ trace }: ReasoningTraceProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-green-700/30 bg-green-950/20 p-3">
      <button className="text-xs uppercase tracking-[0.2em] text-farm-accent" onClick={() => setOpen((prev) => !prev)}>
        {open ? "Hide Reasoning Trace" : "Show Reasoning Trace"}
      </button>
      {open ? (
        <pre className="mt-3 overflow-x-auto rounded-md bg-black/30 p-3 text-xs text-gray-200">
          {JSON.stringify(trace ?? {}, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
