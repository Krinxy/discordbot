"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";

const chartConfig = {
  success: { label: "Success", color: "var(--chart-2)" },
  errors: { label: "Errors", color: "var(--chart-3)" },
} satisfies ChartConfig;

export function ServiceMetricsChart({ data }: { data: { name: string; success: number; errors: number }[] }) {
  const height = Math.max(160, data.length * 40);
  return (
    <ChartContainer config={chartConfig} className="aspect-auto w-full" style={{ height }}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 8, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} strokeDasharray="3 3" />
        <XAxis type="number" tickLine={false} axisLine={false} allowDecimals={false} />
        <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={110} fontSize={11} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="success" stackId="a" fill="var(--color-success)" radius={[4, 0, 0, 4]} />
        <Bar dataKey="errors" stackId="a" fill="var(--color-errors)" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
