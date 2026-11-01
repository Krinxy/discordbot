import { LogChannelForm } from "@/components/log-channel-form";
import { getLogGuilds } from "@/lib/admin-api";

export async function LogPanel() {
  const guilds = await getLogGuilds();

  if (guilds.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        The bot isn&apos;t connected to any guild right now, so there&apos;s nothing to configure yet.
      </p>
    );
  }

  return (
    <div className="flex flex-col divide-y divide-border/60 rounded-2xl border border-border/60">
      {guilds.map((guild) => (
        <div key={guild.guild_id} className="flex items-center justify-between gap-4 p-4">
          <div>
            <p className="text-sm font-medium">{guild.guild_name}</p>
            <p className="text-mono-tabular text-xs text-muted-foreground">
              Current log channel: {guild.log_channel_id ?? "not set"}
            </p>
          </div>
          <LogChannelForm guild={guild} />
        </div>
      ))}
    </div>
  );
}
