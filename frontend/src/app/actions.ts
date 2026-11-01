"use server";

import { revalidatePath } from "next/cache";

import {
  postLogChannel,
  postRssFeed,
  postRssFeedEnabled,
  postTicketStatus,
  postTransferExport,
  type TicketReviewStatus,
} from "@/lib/admin-api";

export async function triggerExportAction() {
  const result = await postTransferExport();
  revalidatePath("/services/transfer");
  return result;
}

export async function setLogChannelAction(guildId: number, channelId: string) {
  const result = await postLogChannel(guildId, channelId);
  revalidatePath("/services/log");
  return result;
}

export async function setTicketStatusAction(ticketId: number, status: TicketReviewStatus) {
  const result = await postTicketStatus(ticketId, status);
  revalidatePath("/services/tickets");
  return result;
}

export async function addRssFeedAction(url: string, channelId: string, name: string) {
  const result = await postRssFeed(url, channelId, name);
  revalidatePath("/services/rss");
  return result;
}

export async function setRssFeedEnabledAction(feedId: number, enabled: boolean) {
  const result = await postRssFeedEnabled(feedId, enabled);
  revalidatePath("/services/rss");
  return result;
}
