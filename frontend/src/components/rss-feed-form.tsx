"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { addRssFeedAction } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function RssFeedForm() {
  const [url, setUrl] = useState("");
  const [channelId, setChannelId] = useState("");
  const [name, setName] = useState("");
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <form
      className="flex flex-wrap items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          try {
            await addRssFeedAction(url.trim(), channelId.trim(), name.trim());
            toast.success(`${name} added.`);
            setUrl("");
            setChannelId("");
            setName("");
            router.refresh();
          } catch (error) {
            toast.error(error instanceof Error ? error.message : "Adding the feed failed.");
          }
        });
      }}
    >
      <Input
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        placeholder="Feed URL (RSS/Atom)"
        className="w-64"
        required
      />
      <Input
        value={channelId}
        onChange={(event) => setChannelId(event.target.value)}
        placeholder="Discord channel ID"
        className="w-40"
        required
      />
      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Name (shown in the embed)"
        className="w-48"
        required
      />
      <Button type="submit" size="sm" disabled={isPending}>
        {isPending ? "Adding…" : "Add feed"}
      </Button>
    </form>
  );
}
