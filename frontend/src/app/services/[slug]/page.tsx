import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ComingSoonPanel } from "@/components/coming-soon-panel";
import { LogPanel } from "@/components/log-panel";
import { RssPanel } from "@/components/rss-panel";
import { ServiceMetricsPanel } from "@/components/service-metrics-panel";
import { SystemLogsPanel } from "@/components/system-logs-panel";
import { Separator } from "@/components/ui/separator";
import { TicketQueuePanel } from "@/components/ticket-queue-panel";
import { TicketTable } from "@/components/ticket-table";
import { TransferPanel } from "@/components/transfer-panel";
import { WatcherTable } from "@/components/watcher-table";
import { getServices } from "@/lib/admin-api";
import { serviceIcons } from "@/lib/icons";
import { defaultAccent, serviceAccents } from "@/lib/service-accents";

function TicketsDetail() {
  return (
    <div className="flex flex-col gap-8">
      <TicketQueuePanel />
      <Separator />
      <div className="flex flex-col gap-3">
        <h2 className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">All tickets</h2>
        <TicketTable />
      </div>
    </div>
  );
}

function DetailBody({ slug, onHold }: { slug: string; onHold: boolean }) {
  if (onHold) {
    return (
      <div className="rounded-2xl border border-border/60 bg-muted/30 p-6 text-sm text-muted-foreground">
        This service is on hold — its import is commented out in{" "}
        <code className="rounded bg-muted px-1 py-0.5">orchestrator/bot.py</code>. Uncomment it there
        and restart the bot to bring it back.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-8">
      <ServiceMetricsPanel slug={slug} />
      <Separator />
      <DetailContent slug={slug} />
    </div>
  );
}

function DetailContent({ slug }: { slug: string }) {
  switch (slug) {
    case "tickets":
      return <TicketsDetail />;
    case "watcher":
      return <WatcherTable />;
    case "transfer":
      return <TransferPanel />;
    case "log":
      return <LogPanel />;
    case "rss":
      return <RssPanel />;
    case "system_logs":
      return <SystemLogsPanel />;
    default:
      return <ComingSoonPanel />;
  }
}

export default async function ServiceDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const tiles = await getServices();
  const tile = tiles.find((entry) => entry.slug === slug);
  if (!tile) {
    notFound();
  }

  const Icon = serviceIcons[tile.icon] ?? serviceIcons.Ticket;
  const accent = serviceAccents[tile.slug] ?? defaultAccent;

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/"
        className="inline-flex w-fit items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> All services
      </Link>
      <div className="flex items-center gap-4">
        <span
          className={`flex h-12 w-12 items-center justify-center rounded-2xl ring-1 ${accent.bg} ${accent.ring}`}
        >
          <Icon className={`h-6 w-6 ${accent.text}`} strokeWidth={1.75} />
        </span>
        <div>
          <h1 className="font-heading text-xl font-semibold tracking-tight">{tile.title}</h1>
          <p className="text-sm text-muted-foreground">{tile.description}</p>
        </div>
      </div>
      <DetailBody slug={slug} onHold={tile.on_hold} />
    </div>
  );
}
