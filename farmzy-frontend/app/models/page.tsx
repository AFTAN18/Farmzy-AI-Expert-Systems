"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useModelStore } from "@/store/model-store";

export default function ModelsPage() {
  const setModelStatus = useModelStore((state) => state.setModelStatus);
  const markRetrained = useModelStore((state) => state.markRetrained);
  const lastRetrained = useModelStore((state) => state.lastRetrained);

  const statusQuery = useQuery({
    queryKey: ["models-status"],
    queryFn: async () => {
      const data = await api.getModels();
      setModelStatus(data);
      return data;
    },
  });

  const retrainMutation = useMutation({
    mutationFn: api.retrainModels,
    onSuccess: () => {
      markRetrained();
      statusQuery.refetch();
    },
  });

  const entries = Object.entries(statusQuery.data ?? {});

  return (
    <div className="space-y-4">
      <button
        className="rounded-md bg-farm-primary px-3 py-2 text-sm text-white"
        onClick={() => retrainMutation.mutate()}
        disabled={retrainMutation.isPending}
      >
        {retrainMutation.isPending ? "Retraining..." : "Retrain Now"}
      </button>

      {lastRetrained ? <p className="text-sm text-gray-400">Last retrained: {new Date(lastRetrained).toLocaleString()}</p> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {entries.map(([name, data]) => {
          const item = data as any;
          return (
            <div key={name} className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-farm-muted">{name}</p>
              <p className="mt-2 text-lg text-farm-accent">{item.version ?? "-"}</p>
              <p className="text-sm text-gray-300">
                {item.metric_name ?? "metric"}: {item.metric_value ?? "-"}
              </p>
              <p className="text-xs text-gray-400">Loaded: {item.loaded ? "Yes" : "No"}</p>
            </div>
          );
        })}
      </section>
    </div>
  );
}
