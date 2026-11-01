"use client";

import { useTransition } from "react";
import { toast } from "sonner";

import { setRssFeedEnabledAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import type { RssFeed } from "@/lib/admin-api";

export function RssFeedToggle({ feed }: { feed: RssFeed }) {
  const [isPending, startTransition] = useTransition();
  const enabled = feed.enabled === 1;

  return (
    <Button
      type="button"
      size="sm"
      variant={enabled ? "outline" : "secondary"}
      disabled={isPending}
      onClick={() => {
        startTransition(async () => {
          try {
            await setRssFeedEnabledAction(feed.id, !enabled);
            toast.success(enabled ? `${feed.name} disabled.` : `${feed.name} enabled.`);
          } catch (error) {
            toast.error(error instanceof Error ? error.message : "Update failed.");
          }
        });
      }}
    >
      {isPending ? "Saving…" : enabled ? "Disable" : "Enable"}
    </Button>
  );
}
