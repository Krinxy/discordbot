import { ServiceTile } from "@/components/service-tile";
import type { MetricsSnapshot, ServiceTile as ServiceTileData } from "@/lib/admin-api";
import { usageForSlug } from "@/lib/service-metrics";

export function ServiceGrid({ tiles, metrics }: { tiles: ServiceTileData[]; metrics: MetricsSnapshot | null }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {tiles.map((tile) => (
        <ServiceTile key={tile.slug} tile={tile} usage={usageForSlug(metrics, tile.slug)} />
      ))}
    </div>
  );
}
