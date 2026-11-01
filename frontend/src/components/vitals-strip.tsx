import { getMetrics, getServices } from "@/lib/admin-api";
import { formatUptime } from "@/lib/service-metrics";

async function loadVitals() {
  try {
    const [services, metrics] = await Promise.all([getServices(), getMetrics()]);
    const totalCalls = Object.values(metrics.calls).reduce((sum, call) => sum + call.count, 0);
    const totalErrors = Object.values(metrics.calls).reduce((sum, call) => sum + call.errors, 0);
    const errorRate = totalCalls > 0 ? (totalErrors / totalCalls) * 100 : 0;
    const activeCount = services.filter((service) => !service.on_hold).length;
    return {
      ok: true as const,
      uptime: formatUptime(metrics.uptime_seconds),
      totalCalls,
      errorRate,
      activeCount,
      totalCount: services.length,
    };
  } catch {
    return { ok: false as const };
  }
}

export async function VitalsStrip() {
  const vitals = await loadVitals();

  if (!vitals.ok) {
    return (
      <div className="flex items-center gap-2 text-mono-tabular text-[11px] text-muted-foreground">
        <span className="h-1.5 w-1.5 rounded-full bg-status-bad" />
        <span>offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-mono-tabular text-[11px] text-muted-foreground">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-status-good opacity-60" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-status-good" />
      </span>
      <span>up {vitals.uptime}</span>
      <span className="text-border">·</span>
      <span>{vitals.totalCalls} calls</span>
      <span className="text-border">·</span>
      <span>{vitals.errorRate.toFixed(1)}% err</span>
      <span className="text-border">·</span>
      <span>
        {vitals.activeCount}/{vitals.totalCount} services
      </span>
    </div>
  );
}
