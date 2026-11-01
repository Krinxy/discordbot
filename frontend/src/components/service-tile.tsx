import Link from "next/link";

import { UsageBadge } from "@/components/usage-badge";
import { Badge } from "@/components/ui/badge";
import type { ServiceTile as ServiceTileData } from "@/lib/admin-api";
import { serviceIcons } from "@/lib/icons";
import { defaultAccent, serviceAccents } from "@/lib/service-accents";
import type { ServiceUsage } from "@/lib/service-metrics";

export function ServiceTile({ tile, usage }: { tile: ServiceTileData; usage: ServiceUsage | null }) {
  const Icon = serviceIcons[tile.icon] ?? serviceIcons.Ticket;
  const accent = serviceAccents[tile.slug] ?? defaultAccent;

  return (
    <Link
      href={`/services/${tile.slug}`}
      className={`group flex flex-col gap-3 rounded-2xl border border-border/60 bg-card p-4 transition-all hover:-translate-y-0.5 hover:border-border hover:shadow-lg ${
        tile.on_hold ? "opacity-60 grayscale hover:opacity-90" : ""
      }`}
    >
      <div className="flex items-start justify-between">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ring-1 ${accent.bg} ${accent.ring}`}>
          <Icon className={`h-4 w-4 ${accent.text}`} strokeWidth={1.75} />
        </span>
        <span
          className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${tile.on_hold ? "bg-status-idle" : "bg-status-good"}`}
          aria-hidden
        />
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-foreground">{tile.title}</span>
        {tile.on_hold ? (
          <Badge variant="secondary" className="w-fit text-[10px] font-normal">
            On hold
          </Badge>
        ) : (
          <UsageBadge usage={usage} />
        )}
      </div>
    </Link>
  );
}
