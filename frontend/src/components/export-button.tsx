"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { toast } from "sonner";

import { triggerExportAction } from "@/app/actions";
import { Button } from "@/components/ui/button";

export function ExportButton() {
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <Button
      disabled={isPending}
      onClick={() =>
        startTransition(async () => {
          try {
            const result = await triggerExportAction();
            toast.success(
              result.count > 0
                ? `Exported ${result.count} request(s) to ${result.path}.`
                : "No open requests to export.",
            );
            router.refresh();
          } catch (error) {
            toast.error(error instanceof Error ? error.message : "Export failed.");
          }
        })
      }
    >
      {isPending ? "Exporting…" : "Export now"}
    </Button>
  );
}
