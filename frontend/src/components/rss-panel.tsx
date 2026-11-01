import { RssFeedForm } from "@/components/rss-feed-form";
import { RssFeedToggle } from "@/components/rss-feed-toggle";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getRssFeeds } from "@/lib/admin-api";

export async function RssPanel() {
  const feeds = await getRssFeeds();

  return (
    <div className="flex flex-col gap-4">
      <RssFeedForm />
      {feeds.length === 0 ? (
        <p className="text-sm text-muted-foreground">No feeds configured yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-border/60">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Feed URL</TableHead>
                <TableHead>Discord channel</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {feeds.map((feed) => (
                <TableRow key={feed.id}>
                  <TableCell className="font-medium">{feed.name}</TableCell>
                  <TableCell className="max-w-xs truncate text-mono-tabular text-muted-foreground">
                    {feed.url}
                  </TableCell>
                  <TableCell className="text-mono-tabular text-muted-foreground">{feed.channel_id}</TableCell>
                  <TableCell>
                    <Badge variant={feed.enabled === 1 ? "default" : "secondary"} className="text-[10px] font-normal">
                      {feed.enabled === 1 ? "Active" : "Disabled"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <RssFeedToggle feed={feed} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
