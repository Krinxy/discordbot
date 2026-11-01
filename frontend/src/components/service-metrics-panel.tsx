import { ServiceInvocationsChart } from "@/components/service-invocations-chart";
import { ServiceMetricsChart } from "@/components/service-metrics-chart";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getMetrics } from "@/lib/admin-api";
import { formatRelativeTime, formatUptime, formatWindow, historyForSlug, usageForSlug } from "@/lib/service-metrics";

export async function ServiceMetricsPanel({ slug }: { slug: string }) {
  const metrics = await getMetrics();
  const usage = usageForSlug(metrics, slug);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Usage</h2>
        <span className="text-mono-tabular text-[11px] text-muted-foreground">
          bot up {formatUptime(metrics.uptime_seconds)}
        </span>
      </div>
      {!usage ? (
        <p className="text-sm text-muted-foreground">No usage recorded yet.</p>
      ) : (
        <>
          <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-card p-4">
            <h3 className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Invocations · last {formatWindow(usage.recentWindowSeconds)}
            </h3>
            <ServiceInvocationsChart history={historyForSlug(metrics, slug)} />
          </div>
          <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-card p-4">
            <h3 className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">By action</h3>
            <ServiceMetricsChart
              data={Object.entries(usage.calls).map(([name, call]) => ({
                name: name.replace(/^event:/, ""),
                success: call.count - call.errors,
                errors: call.errors,
              }))}
            />
          </div>
          <div className="overflow-x-auto rounded-lg border border-border/60">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Action</TableHead>
                  <TableHead>Calls</TableHead>
                  <TableHead>Errors</TableHead>
                  <TableHead>Recent ({formatWindow(usage.recentWindowSeconds)})</TableHead>
                  <TableHead>Avg latency</TableHead>
                  <TableHead>Last called</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(usage.calls).map(([name, call]) => (
                  <TableRow key={name}>
                    <TableCell className="font-medium">{name.replace(/^event:/, "")}</TableCell>
                    <TableCell className="text-mono-tabular">{call.count}</TableCell>
                    <TableCell className="text-mono-tabular">{call.errors}</TableCell>
                    <TableCell className="text-mono-tabular">{call.recent_count}</TableCell>
                    <TableCell className="text-mono-tabular">{call.avg_duration_ms}ms</TableCell>
                    <TableCell className="text-mono-tabular text-muted-foreground">
                      {call.last_called_at ? formatRelativeTime(call.last_called_at) : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}
