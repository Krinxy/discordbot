import type { MetricsCall, MetricsHistoryBucket, MetricsSnapshot } from "@/lib/admin-api";

export const serviceMetricKeys: Record<string, string[]> = {
  music: [
    "idle", "music_play", "music_skip", "music_pause", "music_resume", "music_stop", "music_queue", "troll",
  ],
  tickets: ["event:reaction_add", "event:message"],
  watcher: ["event:message"],
  log: ["event:message_delete", "event:message_edit"],
  transfer: ["event:command_completion"],
  voice_channels: ["event:voice_state_update"],
};

export type ServiceUsage = {
  count: number;
  errors: number;
  errorRate: number;
  lastCalledAt: number | null;
  recentCount: number;
  recentWindowSeconds: number;
  calls: Record<string, MetricsCall>;
};

export function usageForSlug(snapshot: MetricsSnapshot | null, slug: string): ServiceUsage | null {
  if (!snapshot) {
    return null;
  }
  const keys = serviceMetricKeys[slug] ?? [];
  const calls: Record<string, MetricsCall> = {};
  let count = 0;
  let errors = 0;
  let recentCount = 0;
  let lastCalledAt: number | null = null;
  for (const key of keys) {
    const call = snapshot.calls[key];
    if (!call) {
      continue;
    }
    calls[key] = call;
    count += call.count;
    errors += call.errors;
    recentCount += call.recent_count;
    if (call.last_called_at !== null && (lastCalledAt === null || call.last_called_at > lastCalledAt)) {
      lastCalledAt = call.last_called_at;
    }
  }
  if (count === 0) {
    return null;
  }
  return {
    count,
    errors,
    errorRate: errors / count,
    lastCalledAt,
    recentCount,
    recentWindowSeconds: snapshot.recent_window_seconds,
    calls,
  };
}

export function historyForSlug(snapshot: MetricsSnapshot | null, slug: string): MetricsHistoryBucket[] {
  if (!snapshot) {
    return [];
  }
  const keys = serviceMetricKeys[slug] ?? [];
  let merged: MetricsHistoryBucket[] | null = null;
  for (const key of keys) {
    const call = snapshot.calls[key];
    if (!call) {
      continue;
    }
    if (!merged) {
      merged = call.history.map((bucket) => ({ ...bucket }));
    } else {
      call.history.forEach((bucket, index) => {
        merged![index].count += bucket.count;
        merged![index].errors += bucket.errors;
      });
    }
  }
  return merged ?? [];
}

export function formatWindow(seconds: number): string {
  if (seconds % 3600 === 0) {
    return `${seconds / 3600}h`;
  }
  return `${Math.round(seconds / 60)}m`;
}

export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) {
    return `${days}d ${hours}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export function formatRelativeTime(unixSeconds: number): string {
  const diff = Date.now() / 1000 - unixSeconds;
  if (diff < 60) {
    return "just now";
  }
  if (diff < 3600) {
    return `${Math.floor(diff / 60)}m ago`;
  }
  if (diff < 86400) {
    return `${Math.floor(diff / 3600)}h ago`;
  }
  return `${Math.floor(diff / 86400)}d ago`;
}
