import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getSystemLogs, type SystemLogEntry } from "@/lib/admin-api";

const levelVariant: Record<string, "destructive" | "outline" | "secondary" | "ghost"> = {
  CRITICAL: "destructive",
  ERROR: "destructive",
  WARNING: "outline",
  INFO: "secondary",
  DEBUG: "ghost",
};

function shortLoggerName(logger: string) {
  return logger.startsWith("zois.") ? logger.slice("zois.".length) : logger;
}

export async function SystemLogsPanel() {
  const entries: SystemLogEntry[] = await getSystemLogs(200);
  const newestFirst = [...entries].reverse();

  if (newestFirst.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No log lines captured yet — the buffer fills up as the bot runs, it doesn&apos;t replay history from
        before this process started.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        Last {newestFirst.length} log lines from this process, newest first. This is an in-memory ring buffer
        (not a file) — it resets on every restart.
      </p>
      <div className="max-h-[70vh] overflow-y-auto overflow-x-auto rounded-2xl border border-border/60">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Level</TableHead>
              <TableHead>Service</TableHead>
              <TableHead>Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {newestFirst.map((entry, index) => (
              <TableRow key={`${entry.time}-${index}`}>
                <TableCell className="text-mono-tabular whitespace-nowrap text-muted-foreground">
                  {new Date(entry.time).toLocaleTimeString()}
                </TableCell>
                <TableCell>
                  <Badge variant={levelVariant[entry.level] ?? "secondary"} className="text-[10px] font-normal">
                    {entry.level}
                  </Badge>
                </TableCell>
                <TableCell className="text-mono-tabular whitespace-nowrap font-medium">
                  {shortLoggerName(entry.logger)}
                </TableCell>
                <TableCell className="max-w-xl truncate" title={entry.message}>
                  {entry.message}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
