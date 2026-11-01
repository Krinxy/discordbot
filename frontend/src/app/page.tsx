import { Activity, AlertTriangle, Layers, Radio } from "lucide-react";

import { KpiStat } from "@/components/kpi-stat";
import { ServiceGrid } from "@/components/service-grid";
import { getMetrics, getServices, type MetricsSnapshot, type ServiceTile as ServiceTileData } from "@/lib/admin-api";
import { formatUptime } from "@/lib/service-metrics";

export default async function DashboardPage() {
  let tiles: ServiceTileData[] | undefined;
  let metrics: MetricsSnapshot | null = null;
  let loadError: string | null = null;
  try {
    [tiles, metrics] = await Promise.all([getServices(), getMetrics()]);
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Unknown error";
  }

  const calls = metrics ? Object.values(metrics.calls) : [];
  const totalCalls = calls.reduce((sum, call) => sum + call.count, 0);
  const totalErrors = calls.reduce((sum, call) => sum + call.errors, 0);
  const errorRate = totalCalls > 0 ? (totalErrors / totalCalls) * 100 : 0;
  const activeCount = tiles ? tiles.filter((tile) => !tile.on_hold).length : 0;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Everything the bot runs, in one place. Open a tile to view or manage it.
        </p>
      </div>
      {loadError ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
          Could not reach the admin API ({loadError}). Make sure the bot is running and{" "}
          <code className="mx-1 rounded bg-destructive/10 px-1 py-0.5">frontend/.env.local</code>
          matches its <code className="mx-1 rounded bg-destructive/10 px-1 py-0.5">AdminApiKey</code>.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KpiStat
              label="Uptime"
              value={metrics ? formatUptime(metrics.uptime_seconds) : "—"}
              icon={Activity}
              accent
            />
            <KpiStat label="Calls" value={String(totalCalls)} icon={Radio} />
            <KpiStat label="Error rate" value={`${errorRate.toFixed(1)}%`} icon={AlertTriangle} />
            <KpiStat label="Active" value={`${activeCount}/${tiles?.length ?? 0}`} icon={Layers} />
          </div>
          <div className="flex flex-col gap-3">
            <h2 className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Services</h2>
            <ServiceGrid tiles={tiles ?? []} metrics={metrics} />
          </div>
        </>
      )}
    </div>
  );
}
