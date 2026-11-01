import "server-only";

const BASE_URL = process.env.ADMIN_API_BASE_URL;
const API_KEY = process.env.ADMIN_API_KEY;

export type ServiceTile = {
  slug: string;
  title: string;
  description: string;
  icon: string;
  on_hold: boolean;
};

export type ServiceDetail = {
  slug: string;
  on_hold: boolean;
  detail: null;
};

export type Ticket = {
  id: number;
  guild_id: number;
  channel_id: number;
  message_id: number;
  author_id: number;
  author: string;
  content: string;
  status: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  archived_at: string | null;
};

export type WatchedMessage = {
  id: number;
  guild_id: number;
  channel_id: number;
  channel_name: string;
  author_id: number;
  author: string;
  content: string;
  created_at: string;
  message_id: number | null;
};

export type TransferRequest = {
  id: number;
  guild_id: number;
  user_id: number;
  type: string;
  payload: string;
  created_at: string;
  transferred: number;
};

export type TransferSummary = {
  open_count: number;
  requests: TransferRequest[];
};

export type MetricsHistoryBucket = {
  t: number;
  count: number;
  errors: number;
};

export type MetricsCall = {
  count: number;
  errors: number;
  avg_duration_ms: number;
  last_duration_ms: number;
  last_called_at: number | null;
  recent_count: number;
  history: MetricsHistoryBucket[];
};

export type MetricsSnapshot = {
  uptime_seconds: number;
  recent_window_seconds: number;
  bucket_seconds: number;
  calls: Record<string, MetricsCall>;
};

export type TicketReviewStatus = "closed" | "currently_not_possible";

export type LogGuild = {
  guild_id: number;
  guild_name: string;
  log_channel_id: string | null;
};

export type RssFeed = {
  id: number;
  url: string;
  channel_id: string;
  name: string;
  enabled: number;
  created_at: string;
};

export type SystemLogEntry = {
  time: string;
  level: string;
  logger: string;
  message: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE_URL || !API_KEY) {
    throw new Error("ADMIN_API_BASE_URL / ADMIN_API_KEY are not configured in frontend/.env.local");
  }
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`admin API request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getServices() {
  return request<ServiceTile[]>("/services");
}

export function getServiceDetail(slug: string) {
  return request<ServiceDetail>(`/services/${slug}`);
}

export function getMetrics() {
  return request<MetricsSnapshot>("/metrics");
}

export function getTickets() {
  return request<Ticket[]>("/services/tickets");
}

export function getTicketQueue() {
  return request<Ticket[]>("/services/tickets/queue");
}

export function postTicketStatus(ticketId: number, status: TicketReviewStatus) {
  return request<{ id: number; status: string }>(`/services/tickets/${ticketId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export function getWatchedMessages() {
  return request<WatchedMessage[]>("/services/watcher");
}

export function getTransferSummary() {
  return request<TransferSummary>("/services/transfer");
}

export function getLogGuilds() {
  return request<LogGuild[]>("/services/log");
}

export function postTransferExport() {
  return request<{ path: string | null; count: number }>("/services/transfer/export", {
    method: "POST",
  });
}

export function postLogChannel(guildId: number, channelId: string) {
  return request<{ guild_id: number; log_channel_id: string }>(`/services/log/${guildId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel_id: channelId }),
  });
}

export function getRssFeeds() {
  return request<RssFeed[]>("/services/rss");
}

export function postRssFeed(url: string, channelId: string, name: string) {
  return request<RssFeed>("/services/rss", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, channel_id: channelId, name }),
  });
}

export function postRssFeedEnabled(feedId: number, enabled: boolean) {
  return request<{ id: number; enabled: boolean }>(`/services/rss/${feedId}/enabled`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
}

export function getSystemLogs(limit = 200) {
  return request<SystemLogEntry[]>(`/services/logs?limit=${limit}`);
}
