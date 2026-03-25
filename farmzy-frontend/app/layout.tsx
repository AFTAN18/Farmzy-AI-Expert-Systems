"use client";

import { Bell, Brain, ChartBar, Gauge, Leaf, ListChecks, Map, Menu, Radio, ShieldAlert } from "lucide-react";
import { DM_Sans, Space_Mono } from "next/font/google";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useMemo, useState } from "react";

import { Providers } from "@/app/providers";
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
  const unread = useAlertStore((state) => state.unreadCount);

  const selectedFarmName = useMemo(
    () => farms.find((farm) => farm.id === selectedFarmId)?.name ?? "Select Farm",
    [farms, selectedFarmId],
  );

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
        </Providers>
      </body>
    </html>
  );
}
