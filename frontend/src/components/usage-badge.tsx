import { formatRelativeTime, formatWindow, type ServiceUsage } from "@/lib/service-metrics";

export function UsageBadge({ usage }: { usage: ServiceUsage | null }) {
  if (!usage) {
    return <span className="text-mono-tabular text-[11px] text-muted-foreground">no usage yet</span>;
  }
  const errorPct = Math.round(usage.errorRate * 1000) / 10;
  return (
    <div className="flex flex-col gap-0.5 text-mono-tabular text-[11px] text-muted-foreground">
      <span>
        {usage.count} call{usage.count === 1 ? "" : "s"}
        {usage.errors > 0 ? ` · ${errorPct}% err` : ""}
      </span>
      <span className="text-muted-foreground/70">
        {usage.recentCount}/{formatWindow(usage.recentWindowSeconds)}
        {usage.lastCalledAt !== null ? ` · last ${formatRelativeTime(usage.lastCalledAt)}` : ""}
      </span>
    </div>
  );
}
