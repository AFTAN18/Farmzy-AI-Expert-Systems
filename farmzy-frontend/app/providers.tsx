"use client";

import { PropsWithChildren } from "react";

import { QueryProvider } from "@/providers/query-provider";
import { RealtimeProvider } from "@/providers/realtime-provider";

export function Providers({ children }: PropsWithChildren) {
  return (
    <QueryProvider>
      <RealtimeProvider>{children}</RealtimeProvider>
    </QueryProvider>
  );
}
