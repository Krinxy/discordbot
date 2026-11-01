"use client";

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import type { MetricsHistoryBucket } from "@/lib/admin-api";

const chartConfig = {
  count: { label: "Invocations", color: "var(--chart-1)" },
  errors: { label: "Errors", color: "var(--chart-3)" },
} satisfies ChartConfig;

function formatClock(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ServiceInvocationsChart({ history }: { history: MetricsHistoryBucket[] }) {
  const data = history.map((bucket) => ({ ...bucket, label: formatClock(bucket.t) }));

  return (
    <ChartContainer config={chartConfig} className="aspect-auto h-48 w-full">
      <LineChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} interval="preserveStartEnd" fontSize={11} />
        <YAxis tickLine={false} axisLine={false} width={28} allowDecimals={false} fontSize={11} />
        <ChartTooltip content={<ChartTooltipContent labelKey="label" />} />
        <Line type="monotone" dataKey="count" stroke="var(--color-count)" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="errors" stroke="var(--color-errors)" strokeWidth={2} dot={false} />
      </LineChart>
    </ChartContainer>
  );
}
