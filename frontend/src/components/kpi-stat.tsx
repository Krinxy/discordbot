import type { LucideIcon } from "lucide-react";

export function KpiStat({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border/60 bg-card p-4">
      <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <Icon className={`h-3.5 w-3.5 ${accent ? "text-primary" : ""}`} strokeWidth={1.75} />
        <span className="uppercase tracking-wide">{label}</span>
      </div>
      <div className="mt-2 text-mono-tabular text-2xl font-semibold">{value}</div>
    </div>
  );
}
