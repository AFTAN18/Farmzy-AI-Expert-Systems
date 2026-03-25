"use client";

import { useQueryClient } from "@tanstack/react-query";
import { PropsWithChildren, useEffect, useRef } from "react";

import { FarmWebSocket } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import { useAlertStore } from "@/store/alert-store";
import { useFarmStore } from "@/store/farm-store";
import { useSensorStore } from "@/store/sensor-store";

export function RealtimeProvider({ children }: PropsWithChildren) {
  const selectedFarmId = useFarmStore((state) => state.selectedFarmId);
  const pushReading = useSensorStore((state) => state.pushReading);
  const pushAlert = useAlertStore((state) => state.pushAlert);
  const queryClient = useQueryClient();
  const wsRef = useRef<FarmWebSocket | null>(null);

  useEffect(() => {
    wsRef.current = new FarmWebSocket();
    wsRef.current.connect(selectedFarmId, (message) => {
      if (message?.event === "new_reading" && message?.data?.reading) {
        pushReading(message.data.reading);
        queryClient.invalidateQueries({ queryKey: ["dashboard", selectedFarmId] });
        queryClient.invalidateQueries({ queryKey: ["readings", selectedFarmId] });
      }

      if (message?.event === "new_alert" && message?.data) {
        pushAlert(message.data);
        queryClient.invalidateQueries({ queryKey: ["alerts", selectedFarmId] });
      }
    });

    return () => {
      wsRef.current?.disconnect();
      wsRef.current = null;
    };
  }, [selectedFarmId, pushReading, pushAlert, queryClient]);

  useEffect(() => {
    if (!supabase) {
      return;
    }
    const client = supabase;

    const readingChannel = client
      .channel(`sensor_readings_${selectedFarmId}`)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "sensor_readings", filter: `farm_id=eq.${selectedFarmId}` },
        (payload) => {
          if (payload.new) {
            pushReading(payload.new as any);
            queryClient.invalidateQueries({ queryKey: ["dashboard", selectedFarmId] });
          }
        },
      )
      .subscribe();

    const alertChannel = client
      .channel(`alerts_${selectedFarmId}`)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "alerts", filter: `farm_id=eq.${selectedFarmId}` },
        (payload) => {
          if (payload.new) {
            pushAlert(payload.new as any);
          }
        },
      )
      .subscribe();

    return () => {
      client.removeChannel(readingChannel);
      client.removeChannel(alertChannel);
    };
  }, [selectedFarmId, pushReading, pushAlert, queryClient]);

  return <>{children}</>;
}
