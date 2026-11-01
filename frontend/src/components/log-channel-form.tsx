"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { setLogChannelAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { LogGuild } from "@/lib/admin-api";

export function LogChannelForm({ guild }: { guild: LogGuild }) {
  const [value, setValue] = useState(guild.log_channel_id ?? "");
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <form
      className="flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          try {
            await setLogChannelAction(guild.guild_id, value.trim());
            toast.success(`Log channel updated for ${guild.guild_name}.`);
            router.refresh();
          } catch (error) {
            toast.error(error instanceof Error ? error.message : "Update failed.");
          }
        });
      }}
    >
      <Input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Discord channel ID"
        className="w-48"
      />
      <Button type="submit" size="sm" disabled={isPending}>
        {isPending ? "Saving…" : "Save"}
      </Button>
    </form>
  );
}
