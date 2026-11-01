export type ServiceAccent = {
  bg: string;
  text: string;
  ring: string;
};

export const serviceAccents: Record<string, ServiceAccent> = {
  tickets: { bg: "bg-[#c96442]/15", text: "text-[#c96442] dark:text-[#e08363]", ring: "ring-[#c96442]/20" },
  watcher: { bg: "bg-[#a56bb0]/15", text: "text-[#a56bb0] dark:text-[#c98ed4]", ring: "ring-[#a56bb0]/20" },
  transfer: { bg: "bg-[#3f8c7c]/15", text: "text-[#3f8c7c] dark:text-[#5fb4a2]", ring: "ring-[#3f8c7c]/20" },
  log: { bg: "bg-[#756d5e]/15", text: "text-[#756d5e] dark:text-[#a79c89]", ring: "ring-[#756d5e]/20" },
  music: { bg: "bg-[#5b7fa6]/15", text: "text-[#5b7fa6] dark:text-[#82a6cc]", ring: "ring-[#5b7fa6]/20" },
  voice_channels: { bg: "bg-[#6a8f5c]/15", text: "text-[#6a8f5c] dark:text-[#8fbb7f]", ring: "ring-[#6a8f5c]/20" },
  backfill: { bg: "bg-[#a6812f]/15", text: "text-[#a6812f] dark:text-[#c9a66b]", ring: "ring-[#a6812f]/20" },
  imdb: { bg: "bg-[#b06b8a]/15", text: "text-[#b06b8a] dark:text-[#d68eae]", ring: "ring-[#b06b8a]/20" },
  rss: { bg: "bg-[#c97f1b]/15", text: "text-[#c97f1b] dark:text-[#f2a93b]", ring: "ring-[#c97f1b]/20" },
  free_games: { bg: "bg-[#4a9d5f]/15", text: "text-[#4a9d5f] dark:text-[#77c78c]", ring: "ring-[#4a9d5f]/20" },
  twitch_watch: { bg: "bg-[#7c5cd6]/15", text: "text-[#7c5cd6] dark:text-[#a68df0]", ring: "ring-[#7c5cd6]/20" },
  birthdays: { bg: "bg-[#d6608f]/15", text: "text-[#d6608f] dark:text-[#f28bb0]", ring: "ring-[#d6608f]/20" },
  webhooks: { bg: "bg-[#3c9a9a]/15", text: "text-[#3c9a9a] dark:text-[#63c2c2]", ring: "ring-[#3c9a9a]/20" },
  watchlist_export: { bg: "bg-[#b0763f]/15", text: "text-[#b0763f] dark:text-[#d69c66]", ring: "ring-[#b0763f]/20" },
  system_logs: { bg: "bg-[#5c6470]/15", text: "text-[#5c6470] dark:text-[#9aa3b0]", ring: "ring-[#5c6470]/20" },
};

export const defaultAccent: ServiceAccent = {
  bg: "bg-muted",
  text: "text-muted-foreground",
  ring: "ring-border",
};
