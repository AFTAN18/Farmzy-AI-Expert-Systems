"use client";

import { Bell, Brain, ChartBar, Gauge, Leaf, ListChecks, Map, Menu, Radio, Settings2, ShieldAlert } from "lucide-react";
import { DM_Sans, Space_Mono } from "next/font/google";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";

import { Providers } from "@/app/providers";
import { api } from "@/lib/api";
import { useAlertStore } from "@/store/alert-store";
import { useFarmStore } from "@/store/farm-store";

import "./globals.css";

const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-display",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-body",
});

const links = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/sensors", label: "Live Sensor Data", icon: Radio },
  { href: "/predictions", label: "AI Predictions", icon: Brain },
  { href: "/crops", label: "Crop Recommendations", icon: Leaf },
  { href: "/zones", label: "Field Zones", icon: Map },
  { href: "/rules", label: "Expert System Rules", icon: ListChecks },
  { href: "/models", label: "Model Performance", icon: ChartBar },
  { href: "/alerts", label: "Alerts", icon: ShieldAlert },
];

export default function RootLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const [open, setOpen] = useState(true);

  const farms = useFarmStore((state) => state.farms);
  const selectedFarmId = useFarmStore((state) => state.selectedFarmId);
  const setSelectedFarmId = useFarmStore((state) => state.setSelectedFarmId);
  const setFarms = useFarmStore((state) => state.setFarms);
  const unread = useAlertStore((state) => state.unreadCount);

  const [hardwareOpen, setHardwareOpen] = useState(false);
  const [channelId, setChannelId] = useState("");
  const [readApiKey, setReadApiKey] = useState("");
  const [configBusy, setConfigBusy] = useState(false);
  const [syncBusy, setSyncBusy] = useState(false);
  const [hardwareMessage, setHardwareMessage] = useState<string | null>(null);

  const selectedFarmName = useMemo(
    () => farms.find((farm) => farm.id === selectedFarmId)?.name ?? "Select Farm",
    [farms, selectedFarmId],
  );

  useEffect(() => {
    let mounted = true;

    async function loadFarms() {
      try {
        const response = await api.getFarms();
        if (!mounted || !response.items.length) {
          return;
        }
        setFarms(response.items);
        if (!response.items.some((farm) => farm.id === selectedFarmId)) {
          setSelectedFarmId(response.items[0].id);
        }
      } catch {
        // keep local fallback farm list if API is not reachable yet
      }
    }

    loadFarms();
    return () => {
      mounted = false;
    };
  }, [selectedFarmId, setFarms, setSelectedFarmId]);

  async function openHardwareConfig() {
    setHardwareMessage(null);
    setHardwareOpen(true);
    setConfigBusy(true);
    try {
      const config = await api.getFarmThingSpeakConfig(selectedFarmId);
      setChannelId(config.thingspeak_channel_id ?? "");
      setReadApiKey(config.thingspeak_read_api_key ?? "");
    } catch {
      setHardwareMessage("Unable to load farm hardware config.");
    } finally {
      setConfigBusy(false);
    }
  }

  async function saveHardwareConfig() {
    if (!channelId.trim() || !readApiKey.trim()) {
      setHardwareMessage("Channel ID and API key are required.");
      return;
    }

    setConfigBusy(true);
    setHardwareMessage(null);
    try {
      await api.updateFarmThingSpeakConfig(selectedFarmId, {
        thingspeak_channel_id: channelId.trim(),
        thingspeak_read_api_key: readApiKey.trim(),
      });
      const farmsResponse = await api.getFarms();
      setFarms(farmsResponse.items);
      setHardwareMessage("Hardware channel config saved.");
    } catch {
      setHardwareMessage("Failed to save config. Check channel/key and retry.");
    } finally {
      setConfigBusy(false);
    }
  }

  async function syncNow() {
    setSyncBusy(true);
    setHardwareMessage(null);
    try {
      const result = await api.syncFarmNow(selectedFarmId, 20);
      const inserted = (result as { inserted?: number }).inserted ?? 0;
      setHardwareMessage(`Sync completed. New readings processed: ${inserted}.`);
    } catch {
      setHardwareMessage("Manual sync failed. Verify channel ID/API key and hardware feed.");
    } finally {
      setSyncBusy(false);
    }
  }

  return (
    <html lang="en">
      <body className={`${spaceMono.variable} ${dmSans.variable}`}>
        <Providers>
          <div className="flex min-h-screen">
            <aside
              className={`border-r border-green-800/40 bg-farm-surface/95 p-4 transition-all duration-300 ${
                open ? "w-72" : "w-20"
              }`}
            >
              <div className="mb-6 flex items-center justify-between">
                <div className="text-sm font-bold tracking-[0.2em] text-farm-accent">FARMZY</div>
                <button
                  className="rounded-md border border-green-700/40 p-2 text-farm-accent hover:bg-green-900/30"
                  onClick={() => setOpen((prev) => !prev)}
                >
                  <Menu className="h-4 w-4" />
                </button>
              </div>

              <nav className="space-y-2">
                {links.map((link) => {
                  const Icon = link.icon;
                  const active = pathname.startsWith(link.href);
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                        active
                          ? "bg-green-500/15 text-farm-accent shadow-glow"
                          : "text-gray-300 hover:bg-green-900/20 hover:text-farm-accent"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {open ? link.label : null}
                    </Link>
                  );
                })}
              </nav>
            </aside>

            <main className="flex-1 p-5">
              <header className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-green-800/30 bg-farm-surface/90 p-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.25em] text-farm-muted">Precision Agriculture Console</p>
                  <h1 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                    {selectedFarmName}
                  </h1>
                </div>

                <div className="flex items-center gap-3">
                  <select
                    className="rounded-lg border border-green-700/50 bg-green-950/40 px-3 py-2 text-sm"
                    value={selectedFarmId}
                    onChange={(event) => setSelectedFarmId(event.target.value)}
                  >
                    {farms.map((farm) => (
                      <option key={farm.id} value={farm.id}>
                        {farm.name}
                      </option>
                    ))}
                  </select>

                  <button
                    className="inline-flex items-center gap-2 rounded-lg border border-green-700/50 bg-green-900/20 px-3 py-2 text-xs text-farm-accent"
                    onClick={openHardwareConfig}
                  >
                    <Settings2 className="h-4 w-4" />
                    Hardware Setup
                  </button>

                  <div className="flex items-center gap-2 rounded-full border border-green-700/50 bg-green-900/20 px-3 py-1 text-xs">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-farm-accent" />
                    Connected
                  </div>

                  <div className="relative rounded-full border border-green-700/50 bg-green-900/20 p-2 text-farm-accent">
                    <Bell className="h-4 w-4" />
                    {unread > 0 ? (
                      <span className="absolute -right-1 -top-1 rounded-full bg-farm-danger px-1.5 text-[10px] text-white">
                        {unread}
                      </span>
                    ) : null}
                  </div>
                </div>
              </header>

              {children}
            </main>
          </div>

          {hardwareOpen ? (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
              <div className="w-full max-w-lg rounded-xl border border-green-700/40 bg-farm-surface p-5 shadow-glow">
                <div className="mb-4">
                  <h2 className="text-lg font-semibold text-farm-accent">Hardware Channel Setup</h2>
                  <p className="text-sm text-gray-300">
                    Add ThingSpeak Channel ID and Read API key to pull sensor values, predictions, and alerts.
                  </p>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-xs uppercase tracking-[0.2em] text-farm-muted">ThingSpeak Channel ID</label>
                    <input
                      className="w-full rounded-lg border border-green-700/50 bg-green-950/30 px-3 py-2 text-sm text-gray-100"
                      value={channelId}
                      onChange={(event) => setChannelId(event.target.value)}
                      placeholder="e.g. 2972911"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-xs uppercase tracking-[0.2em] text-farm-muted">ThingSpeak Read API Key</label>
                    <input
                      className="w-full rounded-lg border border-green-700/50 bg-green-950/30 px-3 py-2 text-sm text-gray-100"
                      value={readApiKey}
                      onChange={(event) => setReadApiKey(event.target.value)}
                      placeholder="Paste Read API key"
                    />
                  </div>

                  {hardwareMessage ? <p className="text-xs text-farm-accent">{hardwareMessage}</p> : null}
                </div>

                <div className="mt-5 flex flex-wrap justify-end gap-2">
                  <button
                    className="rounded-md border border-green-700/50 px-3 py-2 text-sm text-gray-200"
                    onClick={() => setHardwareOpen(false)}
                  >
                    Close
                  </button>
                  <button
                    className="rounded-md border border-green-600/60 bg-green-900/40 px-3 py-2 text-sm text-farm-accent"
                    onClick={syncNow}
                    disabled={syncBusy || configBusy}
                  >
                    {syncBusy ? "Syncing..." : "Sync Now"}
                  </button>
                  <button
                    className="rounded-md bg-farm-primary px-3 py-2 text-sm text-white"
                    onClick={saveHardwareConfig}
                    disabled={configBusy}
                  >
                    {configBusy ? "Saving..." : "Save Config"}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </Providers>
      </body>
    </html>
  );
}
